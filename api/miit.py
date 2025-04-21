import base64
import hashlib
import json
import random
import time

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from pydantic import BaseModel

from api.crack import Crack


class Captcha(BaseModel):
    uuid: str
    bigImage: str
    smallImage: str
    secretKey: str
    wordCount: int


class QueryResult(BaseModel):
    contentTypeName: str
    domain: str
    domainId: int
    leaderName: str
    limitAccess: str
    mainId: int
    mainLicence: str
    natureName: str
    serviceId: int
    serviceLicence: str
    unitName: str
    updateRecordTime: str


class MiitApi(httpx.AsyncClient):
    token: str

    def __init__(self):
        self.crack = Crack()
        super().__init__(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32",
                "Origin": "https://beian.miit.gov.cn",
                "Referer": "https://beian.miit.gov.cn/",
            },
        )


    async def setup_cookie(self):
        await self.get("https://beian.miit.gov.cn/")
        assert self.cookies.get("__jsluid_s", None) is not None

    async def __aenter__(self):
        await super().__aenter__()
        await self.setup_cookie()
        self.token = await self.get_token()
        return self

    async def get_token(self):
        timeStamp = round(time.time() * 1000)
        authSecret = "testtest" + str(timeStamp)
        authKey = hashlib.md5(authSecret.encode(encoding="UTF-8")).hexdigest()
        res = await self.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/auth",
            data={"authKey": authKey, "timeStamp": timeStamp},
        )
        res.raise_for_status()
        t = res.json()

        return t["params"]["bussiness"]

    async def get_client_uid(self):
        characters = "0123456789abcdef"
        unique_id = ["0"] * 36

        for i in range(36):
            unique_id[i] = random.choice(characters)

        unique_id[14] = "4"
        unique_id[19] = characters[(3 & int(unique_id[19], 16)) | 8]
        unique_id[8] = unique_id[13] = unique_id[18] = unique_id[23] = "-"

        point_id = "point-" + "".join(unique_id)

        return point_id

    async def solve_captcha(self) -> str:
        client_uid = await self.get_client_uid()
        res = await self.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/getCheckImagePoint",
            json={"clientUid": client_uid},
            headers={
                "Token": self.token,
            },
        )
        res.raise_for_status()

        captcha = Captcha.model_validate(res.json()["params"])

        r = self.generate_pointjson(
            captcha.bigImage, captcha.smallImage, captcha.secretKey
        )

        res = await self.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/checkImage",
            json={
                "token": captcha.uuid,
                "secretKey": captcha.secretKey,
                "clientUid": client_uid,
                "pointJson": r,
            },
            headers={
                "Token": self.token,
            },
        )

        res.raise_for_status()

        if not res.json()["success"]:
            raise ValueError("captcha failed")

        return res.json()["params"]["sign"]

    def generate_pointjson(self, big_img, small_img, secret_key: str):
        boxes = self.crack.detect(big_img)
        points = self.crack.siamese(small_img, boxes)
        new_points = [[p[0] + 20, p[1] + 20] for p in points]
        pointJson = [{"x": p[0], "y": p[1]} for p in new_points]
        cipher = AES.new(secret_key.encode(), AES.MODE_ECB)
        ciphertext = cipher.encrypt(
            pad(json.dumps(pointJson, separators=(",", ":")).encode(), AES.block_size)
        )
        return base64.b64encode(ciphertext).decode()

    async def query(self, sign: str, domain: str):
        headers = {
            "Token": self.token,
            "Sign": sign,
        }

        data = {"pageNum": "", "pageSize": "", "unitName": domain, "serviceType": 1}
        resp = await self.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition/",
            headers=headers,
            json=data,
        )

        resp.raise_for_status()
        d = resp.json()

        if not d["success"]:
            raise ValueError(f"query failed: {d['msg']}")
        if d["params"]["total"] == 0:
            return None
        return QueryResult.model_validate(d["params"]["list"][0])


if __name__ == "__main__":

    async def main():
        async with MiitApi() as client:
            # auth = await client.solve_captcha()
            auth = "eyJ0eXBlIjozLCJleHREYXRhIjp7InZhZnljb2RlX2ltYWdlX2tleSI6IjZiZGNjY2U2NDI4MjRjYzA5ZjQ5OWY1Y2RkYmJiNWM4In0sImUiOjE3NDUyMDM1NzQ4MDV9.GKmKKgseF6zT0k_hrMtdcIBokZYSk3O5-LOgtTiPYjA"
            print(auth)
            print(await client.query(auth, "baidu.com"))

    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

import base64
import hashlib
import random
import time
from asyncio import sleep
from pathlib import Path

import httpx
from pydantic import BaseModel


class Captcha(BaseModel):
    uuid: str
    bigImage: str
    smallImage: str
    secretKey: str
    wordCount: int


class MiitApi(httpx.AsyncClient):
    token: str

    def __init__(self):
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

    async def get_captcha(self) -> Captcha:
        client_uid = await self.get_client_uid()
        res = await self.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/getCheckImagePoint",
            json={"clientUid": client_uid},
            headers={
                "Token": self.token,
            },
        )
        res.raise_for_status()

        return Captcha.model_validate(res.json()["params"])


async def main():
    data_dir = Path("data")

    for i in range(100):
        async with MiitApi() as api:
            for i in range(8):
                captcha = await api.get_captcha()
                big_image_data = base64.b64decode(captcha.bigImage)
                small_image_data = base64.b64decode(captcha.smallImage)

                (data_dir / "big").mkdir(parents=True, exist_ok=True)
                (data_dir / "small").mkdir(parents=True, exist_ok=True)

                with open(data_dir / "big" / f"{captcha.uuid}.png", "wb") as f:
                    f.write(big_image_data)

                with open(data_dir / "small" / f"{captcha.uuid}.png", "wb") as f:
                    f.write(small_image_data)

                print(f"Saved captcha {i + 1}/100: {captcha.uuid}")
            await sleep(30)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

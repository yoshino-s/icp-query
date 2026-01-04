import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import verboselogs
from fastapi import Depends, FastAPI, HTTPException

from .api.miit import MiitApi
from .config import load_config
from .dao.query import QueryResponse
from .db.db import IcpRecord, get_engine, init_db
from .db.query import Query

cm = load_config()


class AuthPool(MiitApi):
    pool: set[tuple[str, str]]
    lock: asyncio.Lock
    logger = verboselogs.VerboseLogger("AuthPool")

    def __init__(self):
        super().__init__()
        self.pool = set()
        self.lock = asyncio.Lock()

    async def get_auth(self):
        async with self.lock:
            if not self.pool:
                while True:
                    try:
                        uuid, auth = await self.solve_captcha()
                        self.pool.add((uuid, auth))
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to get auth: {e}")
                        await asyncio.sleep(1)
            # get one auth from pool
            return self.pool.pop()

    async def return_auth(self, uuid: str, auth: str):
        async with self.lock:
            self.pool.add((uuid, auth))


auth_pool: Optional["AuthPool"] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global auth_pool
    auth_pool = AuthPool()

    await init_db(cm.database)

    async with auth_pool:
        yield


app = FastAPI(lifespan=lifespan)


async def auth_pool_dep():
    if auth_pool is None:
        raise RuntimeError("Auth pool has not been started")
    return auth_pool


AuthPoolDep = Depends(auth_pool_dep)


async def query_dep():
    return Query(get_engine())


QueryDep = Depends(query_dep)


@app.get("/solve_captcha")
async def solve_captcha(auth_pool: AuthPool = AuthPoolDep):
    uuid, auth = await auth_pool.get_auth()
    return {"uuid": uuid, "auth": auth}


@app.get("/query", response_model=QueryResponse)
async def query_icp(
    name: str, auth_pool: AuthPool = AuthPoolDep, query: Query = QueryDep
):
    if (cached := await query.get(name)) is not None:
        return QueryResponse(cached=True, record=cached)

    uuid, auth = await auth_pool.get_auth()
    try:
        res = await auth_pool.query(uuid, auth, name)
        await auth_pool.return_auth(uuid, auth)
    except Exception as e:
        raise e

    if res is not None and len(res) > 0:
        record = IcpRecord.from_query_result(res[0])
        await query.save(record)
        return QueryResponse(cached=False, record=record)
    else:
        raise HTTPException(404, "not found")

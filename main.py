from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.miit import MiitApi

current_sign = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global current_sign
    async with MiitApi() as api:
        while True:
            try:
                current_sign = await api.solve_captcha()
                break
            except ValueError:
                pass
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/sign")
async def get_sign():
    global current_sign
    return current_sign


@app.get("/query")
async def query(domain: str):
    global current_sign
    async with MiitApi() as api:
        result = await api.query(current_sign, domain)

    return result

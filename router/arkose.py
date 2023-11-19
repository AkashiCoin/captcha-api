import time
from loguru import logger
from pydantic import BaseModel

from fastapi import APIRouter
from .utils import CaptchaResponse, make_response
from utils.async_solver import solver

arkose_route = APIRouter()
token_route = APIRouter(prefix="/token/arkose")

base_payload = {
    "url": "https://chat.openai.com/",
    "subdomain": "tcr9i.chat.openai.com"
}
gpt3_payload = {
    "publickey": "3D86FBBA-9D22-402A-B512-3420086BA6CC",
    **base_payload
}
gpt4_payload = {
    "publickey": "35536E1E-65B4-4D96-9D97-6ADB7EFF8147",
    **base_payload
}
auth_payload = {
    "publickey": "0A1D34FC-659D-4E23-B17B-694DCFCF6A6C",
    **base_payload
}


class SolveRequest(BaseModel):
    publickey: str
    url: str
    subdomain: str = "tcr9i.chat.openai.com"


def build_page_data(publickey: str, subdomain: str):
    page_data = solver.page_data.replace("<publickey>", publickey)
    page_data = page_data.replace("<subdomain>", subdomain)
    return page_data


@token_route.post("/solve", response_model=CaptchaResponse)
async def solve(req: SolveRequest):
    publickey = req.publickey
    url = req.url
    subdomain = req.subdomain
    start_time = time.time()
    token = await solver.solve(url, build_page_data(publickey, subdomain))
    end_time = time.time() - start_time
    logger.info(f"took {end_time} seconds :: " + token[:10])
    return make_response(token, end_time)


@token_route.get("/gpt3", response_model=CaptchaResponse)
async def _():
    return await solve(SolveRequest(**gpt3_payload))


@token_route.get("/gpt4", response_model=CaptchaResponse)
async def _():
    return await solve(SolveRequest(**gpt4_payload))


@token_route.get("/auth", response_model=CaptchaResponse)
async def _():
    return await solve(SolveRequest(**auth_payload))


arkose_route.include_router(token_route)

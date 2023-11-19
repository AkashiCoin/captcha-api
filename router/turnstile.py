import time
from loguru import logger
from pydantic import BaseModel

from fastapi import APIRouter
from .utils import make_response, CaptchaResponse
from utils.async_solver import solver

turnstile_route = APIRouter()
token_route = APIRouter(prefix="/token/turnstile")

base_payload = {
    "url": "https://chat.openai.com/",
    "subdomain": "tcr9i.chat.openai.com"
}

class SolveRequest(BaseModel):
    sitekey: str
    url: str
    invisible: bool = False


def build_page_data(sitekey: str, invisible: bool):
    page_data = solver.page_data.replace("<turnstile>", "challenges.cloudflare.com")
    page_data = page_data.replace("<sitekey>", sitekey)
    # page_data = page_data.replace("<subdomain>", subdomain)
    return page_data


@token_route.post("/solve", response_model=CaptchaResponse)
async def solve(req: SolveRequest):
    sitekey = req.sitekey
    url = req.url
    invisible = req.invisible
    start_time = time.time()
    token = await solver.solve(url, build_page_data(sitekey=sitekey, invisible=invisible))
    end_time = time.time() - start_time
    logger.info(f"took {end_time} seconds :: " + token[:10])
    return make_response(token, end_time)


turnstile_route.include_router(token_route)

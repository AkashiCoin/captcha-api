import time
import re
import aiohttp

from urllib.parse import urlencode
from loguru import logger
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from utils.async_solver import AsyncSolver, solver
from .utils import CaptchaResponse, make_response
from config import PROXIES


recaptcha_route = APIRouter()
token_route = APIRouter(prefix="/token/recaptcha")
pixiv_loigin_payload = {
    "sitekey": "6LfF1dcZAAAAAOHQX8v16MX5SktDwmQINVD_6mBF",
    "url": "https://accounts.pixiv.net/login",
    "action": "accounts/login",
}


class SolveRequest(BaseModel):
    sitekey: str
    url: str
    action: str


def build_page_data(sitekey, action):
    page_data = solver.page_data.replace("<recaptcha>", "www.recaptcha.net")
    page_data = page_data.replace("<sitekey>", sitekey)
    page_data = page_data.replace("<action>", action)
    return page_data


@token_route.post("/solve", response_model=CaptchaResponse)
async def solve(req: SolveRequest):
    sitekey = req.sitekey
    url = req.url
    action = req.action
    start_time = time.time()
    token = await solver.solve(url, build_page_data(sitekey, action))
    end_time = time.time() - start_time
    logger.info(f"took {end_time} seconds :: " + token[:10])
    return make_response(token, end_time)


@token_route.get("/pixiv/login", response_model=CaptchaResponse)
async def _():
    return await solve(SolveRequest(**pixiv_loigin_payload))


@recaptcha_route.post("/api/pixiv/login")
async def _(login_id: str = Form(...), password: str = Form(...)):
    done = False
    if len(login_id) < 6 or len(password) < 6:
        message = "(`皿´)账号或者密码至少为6位数"
    else:
        done, message = await login(
            solver,
            "http://" + PROXIES,
            login_id,
            password,
        )
    if done:
        response = RedirectResponse("/", 302)
        response.set_cookie("PHPSESSID", message)
    else:
        response = RedirectResponse(f"/login.html?error={message}", 302)
    return response


recaptcha_route.include_router(token_route)
url = "https://accounts.pixiv.net/ajax/login?lang=zh"

headers = {
    "authority": "accounts.pixiv.net",
    "accept": "application/json",
    "accept-language": "zh-CN,zh;q=0.9,ko;q=0.8",
    "cache-control": "max-age=0",
    "dnt": "1",
    "origin": "https://accounts.pixiv.net",
    "referer": "https://accounts.pixiv.net/login?return_to=https%3A%2F%2Fwww.pixiv.net%2F&lang=zh&source=accounts&view_type=page&ref=",
    "sec-ch-ua": '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "content-type": "application/x-www-form-urlencoded",
    "Host": "accounts.pixiv.net",
    "Connection": "keep-alive",
}


async def login(solver: AsyncSolver, proxy: str, login_id: str, password: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(pixiv_loigin_payload["url"], proxy=proxy) as resp:
                text = await resp.text()
                csrf_token = re.search(r'tt":"(.*?)"', text).group(1)
                token = await solver.solve(
                    url=pixiv_loigin_payload["url"],
                    page_data=build_page_data(
                        pixiv_loigin_payload["sitekey"], pixiv_loigin_payload["action"]
                    ),
                )
                payload = {
                    "login_id": login_id,
                    "password": password,
                    "source": "accounts",
                    "app_ios": "0",
                    "ref": "",
                    "return_to": "https://www.pixiv.net/",
                    "g_recaptcha_response": "",
                    "tt": csrf_token,
                    "recaptcha_enterprise_score_token": token,
                }
                async with session.post(
                    url=url, headers=headers, data=urlencode(payload), proxy=proxy
                ) as res:
                    if res.status == 200 and res.cookies.get("PHPSESSID"):
                        return True, res.cookies.get("PHPSESSID")
                    else:
                        if res.content_type == "application/json":
                            data = await res.json()
                            logger.info(data)
                            if data.get("error"):
                                message = data.get("message")
                            else:
                                _body = data.get("body")
                                if _body:
                                    errors = _body.get("errors")
                                    if errors:
                                        if other := errors.get("other"):
                                            if other.find("verifyFailed"):
                                                message = "ヽ(`Д´)ﾉ账号密码错误!"
                                            else:
                                                message = f"(ﾟ▽ﾟ*) 未知错误: {other}"
                                        elif errors.get("recaptcha"):
                                            message = "T^T ReCaptcha验证失败，请重试"
                                        elif errors.get("requireExtraVerification"):
                                            message = f"(Ｔ▽Ｔ)你的账号需要二步验证，暂不支持, token: {errors.get('requireExtraVerification')}"
                                        else:
                                            message = f"(ﾟ▽ﾟ*) 未知错误: {errors}"
                                    else:
                                        message = _body
                                else:
                                    message = data
                            return False, message
                        else:
                            return False, await res.text()
    except Exception as e:
        return False, f"o(╥﹏╥)o服务器出现了问题: {e}"

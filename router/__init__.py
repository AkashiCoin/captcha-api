import playwright.async_api

from fastapi import FastAPI
from utils.async_solver import solver
from .arkose import arkose_route
from .recaptcha import recaptcha_route
from .turnstile import turnstile_route

app = FastAPI()


@app.on_event("startup")
async def _():
    p = await playwright.async_api.async_playwright().start()
    await solver.start_browser(p)
    app.include_router(arkose_route)
    app.include_router(recaptcha_route)
    app.include_router(turnstile_route)


@app.get("/")
async def index():
    return {"status": "success"}

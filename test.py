import asyncio
import playwright.async_api

from utils.async_solver import solver
from router.arkose import build_page_data as arkose_build
from router.recaptcha import build_page_data as recaptcha_build
from router.turnstile import build_page_data as turnstile_build


async def arkose_test():
    url = "https://chat.openai.com/"
    publickey = "35536E1E-65B4-4D96-9D97-6ADB7EFF8147"
    subdomain = "tcr9i.chat.openai.com"
    print(
        await solver.solve(
            url=url, page_data=arkose_build(publickey=publickey, subdomain=subdomain)
        )
    )


async def recaptcha_test():
    url = "https://accounts.pixiv.net/login"
    sitekey = "6LfF1dcZAAAAAOHQX8v16MX5SktDwmQINVD_6mBF"
    action = "accounts/login"
    print(
        await solver.solve(
            url=url, page_data=recaptcha_build(sitekey=sitekey, action=action)
        )
    )


async def turnstile_test():
    url = "https://modrinth.com/auth/sign-up"
    sitekey = "0x4AAAAAAAHWfmKCm7cUG869"
    invisible = False
    print(
        await solver.solve(
            url=url, page_data=turnstile_build(sitekey=sitekey, invisible=invisible)
        )
    )


async def main():
    global solver
    p = await playwright.async_api.async_playwright().start()
    await solver.start_browser(p)
    await arkose_test()
    await recaptcha_test()
    await turnstile_test()


if __name__ == "__main__":
    asyncio.run(main())

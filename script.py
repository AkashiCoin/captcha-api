import playwright.async_api
import argparse
from router.arkose import build_page_data
from utils.async_solver import solver


async def init_har():
    p = await playwright.async_api.async_playwright().start()
    await solver.start_browser(p)
    url = "https://chat.openai.com/"
    subdomain = "tcr9i.chat.openai.com"
    for publickey in [
        "3D86FBBA-9D22-402A-B512-3420086BA6CC",
        "35536E1E-65B4-4D96-9D97-6ADB7EFF8147",
        "0A1D34FC-659D-4E23-B17B-694DCFCF6A6C",
    ]:
        token = await solver.solve(
            url,
            build_page_data(publickey, subdomain),
            har=True,
            filename=publickey,
        )
        if token != "failed":
            print(f"Success create har file: {publickey}.har, temp token: {token[:10]}")
        else:
            print(f"Faild create har file: {publickey}.har")


def main():
    parse = argparse.ArgumentParser()
    parse.add_argument("cmd", help="har")
    args = parse.parse_args()
    if args.cmd:
        cmd = args.cmd
        if cmd == "har":
            import asyncio

            asyncio.get_event_loop().run_until_complete(init_har())
        else:
            print("Unknown command")


if __name__ == "__main__":
    main()

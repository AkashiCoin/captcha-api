import asyncio
import json
import random
import os
import pickle

from urllib.parse import parse_qs, urlparse, urlunparse

from playwright.async_api import (
    Playwright,
    async_playwright,
    Browser,
    Route,
    BrowserContext,
    Page,
    Request,
)

from config import CAPTCHA_PROXY, PROXIES, HEADLESS, HAR_DIR, TEMP_CACHE_FILE


class AsyncSolver:
    def __init__(self, proxy="", headless=True, cache_file: str = TEMP_CACHE_FILE):
        self.proxy = proxy
        self.headless = headless
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page_data: str = ""
        self.cache_file: str = os.path.abspath(cache_file)
        self.cache: dict = self.load_cache_data()
        self.load_page_data()

    async def terminate(self):
        await self.browser.close()

    def load_page_data(self):
        with open("utils/page.html") as f:
            self.page_data = f.read()

    def load_cache_data(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                cache = pickle.load(f)
        else:
            cache = {}
            self.write_cache_data(cache)
        return cache

    def write_cache_data(self, cache: dict):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "wb") as f:
            pickle.dump(cache, f)

    def get_mouse_path(self, x1, y1, x2, y2):
        # calculate the path to x2 and y2 from x1 and y1
        path = []
        x = x1
        y = y1
        while abs(x - x2) > 3 or abs(y - y2) > 3:
            diff = abs(x - x2) + abs(y - y2)
            speed = random.randint(1, 2)
            if diff < 20:
                speed = random.randint(1, 3)
            else:
                speed *= diff / 45

            if abs(x - x2) > 3:
                if x < x2:
                    x += speed
                elif x > x2:
                    x -= speed
            if abs(y - y2) > 3:
                if y < y2:
                    y += speed
                elif y > y2:
                    y -= speed
            path.append((x, y))

        return path

    async def move_to(self, page: Page, current_x, current_y, x, y):
        for path in self.get_mouse_path(current_x, current_y, x, y):
            await page.mouse.move(path[0], path[1])
            if random.randint(0, 100) > 15:
                await asyncio.sleep(random.randint(1, 5) / random.randint(400, 600))

    async def solve_invisible(self, page: Page):
        iterations = 0

        window_width = await page.evaluate("window.innerWidth")
        window_height = await page.evaluate("window.innerHeight")
        current_x = 0
        current_y = 0

        while iterations < 10:
            random_x = random.randint(0, window_width)
            random_y = random.randint(0, window_height)
            iterations += 1

            await self.move_to(page, current_x, current_y, random_x, random_y)
            current_x = random_x
            current_y = random_y
            elem = await page.query_selector("[id=captcha-token]")
            if elem:
                token = await elem.evaluate("textarea => textarea.value")
                if token:
                    return token
            await asyncio.sleep(random.randint(2, 5) / random.randint(400, 600))
        return "failed"

    async def solve(
        self, url: str, page_data: str, har: bool = False, filename: str = ""
    ):
        url = url + "/" if not url.endswith("/") else url
        if not self.browser:
            await self.start_browser(self.playwright)

        async def route_handler(route: Route):
            await route.fulfill(body=page_data, status=200)

        context = await self.init_context(har=har, filename=filename)
        page = await context.new_page()
        await page.route(url, route_handler)
        await page.goto(url)

        output = await self.solve_invisible(page)
        # await asyncio.sleep(100)

        await page.close()
        await context.close()
        if har:
            self.parse_and_save_post_data(filename)
        return output

    @staticmethod
    def parse_and_save_post_data(filename: str):
        har_file_path = f"{HAR_DIR}/{filename}.har"
        with open(har_file_path, "r") as f:
            har_dict = json.load(f)

        for entry in har_dict["log"]["entries"]:
            request = entry["request"]
            if "postData" in request:
                post_data = request["postData"]
                if post_data["mimeType"].startswith(
                    "application/x-www-form-urlencoded"
                ):
                    params = parse_qs(post_data["text"])
                    for k, v in params.items():
                        post_data["params"].append({"name": k, "value": v[0]})

        # 将修改后的HAR字典保存回HAR文件中
        with open(har_file_path, "w") as f:
            json.dump(har_dict, f, ensure_ascii=False, indent=4)

    async def route_cache_handler(self, route: Route, request: Request):
        # 如果请求的 URL 已经在缓存中，那么就直接返回缓存的内容
        if request.method != "GET":
            return await route.continue_()
        if request.url in self.cache:
            await route.fulfill(**self.cache[request.url])
        else:
            # 否则，继续网络请求，并将响应的内容存入缓存
            await route.continue_()
            response = await request.response()
            if response:
                await response.finished()
                if response.status != 200:
                    return
                resp = {
                    "status": response.status,
                    "headers": response.headers,
                    "body": await response.body()
                }
                self.cache[request.url] = resp
                self.write_cache_data(self.cache)

    async def handle_captcha(self, route: Route, request: Request):
        url = f"{CAPTCHA_PROXY}{request.url}"
        await route.continue_(
            url=url,
            method=request.method,
            headers={**request.headers, "Host": urlparse(url).netloc},
            post_data=request.post_data_buffer,
        )

    async def init_context(self, har: bool = False, filename: str = ""):
        ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/{self.browser.version}"
        context = await self.browser.new_context(
            user_agent=ua,
            bypass_csp=True,
            record_har_path=f"{HAR_DIR}/{filename}.har" if har else None,
            record_har_url_filter="https://tcr9i.chat.openai.com/fc/gt2/public_key/**"
            # record_har_content="omit",
        )
        if not har:
            await context.route("**/reload?**", self.handle_captcha)
            await context.route("**/fc/gt2/public_key/*", self.handle_captcha)
        await context.route("**/*.js**", self.route_cache_handler)
        await context.route("**/*.css**", self.route_cache_handler)
        await context.route("**/*.html**", self.route_cache_handler)
        await context.route("**/*.json**", self.route_cache_handler)
        await context.route("**/*.png**", self.route_cache_handler)
        await context.route("**/*.woff2**", self.route_cache_handler)

        await context.route("**/anchor?**", self.route_cache_handler)
        await context.route("**/*.ico**", lambda route: route.abort())
        await context.route("**/settings", lambda route: route.abort())
        await context.route("**/fc/a/?**", lambda route: route.abort())
        return context

    async def start_browser(self, playwright: Playwright):
        if self.proxy:
            self.browser = await playwright.firefox.launch(
                headless=self.headless,
                proxy={
                    "server": "http://" + self.proxy.split("@")[1],
                    "username": self.proxy.split("@")[0].split(":")[0],
                    "password": self.proxy.split("@")[0].split(":")[1],
                },
            )
        else:
            self.browser = await playwright.firefox.launch(headless=self.headless)

        self.context = await self.init_context()


solver: AsyncSolver = AsyncSolver(f":@{PROXIES}" if PROXIES else "", HEADLESS)

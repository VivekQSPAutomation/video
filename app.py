import sys
import asyncio
from playwright.async_api import async_playwright


async def run_playwright(url: str, browser_type: str):
    async with async_playwright() as p:
        if browser_type == "firefox":
            browser = await p.firefox.launch()
        elif browser_type == "webkit":
            browser = await p.webkit.launch()
        else:
            browser = await p.chromium.launch()

        page = await browser.new_page()
        await page.goto(url)

        print(f"Title of {url}: {await page.title()}")

        await browser.close()


if __name__ == "__main__":
    # Get URL and browser type from command-line arguments
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    browser_type = sys.argv[2] if len(sys.argv) > 2 else "chromium"

    asyncio.run(run_playwright(url, browser_type))

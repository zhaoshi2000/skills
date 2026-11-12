import os
from pathlib import Path
from playwright.async_api import async_playwright
from .cookies import load_bilibili_cookies
from .logging import say

PROFILE = str(Path("data/browser_profile").resolve())


async def _launch_context(playwright):
    cookies = load_bilibili_cookies()
    options = {"headless": False}
    channel = os.getenv("BROWSER_CHANNEL", "").strip()
    if not channel and Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists():
        channel = "chrome"
    if channel:
        options["channel"] = channel
    ctx = await playwright.chromium.launch_persistent_context(PROFILE, **options)
    if cookies:
        try:
            await ctx.add_cookies(cookies)
        except Exception:
            await ctx.close()
            raise
    return ctx

async def login():
    Path(PROFILE).mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        ctx = await _launch_context(p)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://www.bilibili.com/", wait_until="domcontentloaded")
        say("登录", "请在浏览器中手动登录B站，完成后回到终端按回车。", "yellow")
        input()
        await ctx.close()
        say("登录", "浏览器会话保存在 data/browser_profile。请勿分享此目录。", "green")

async def get_feed(limit=30):
    async with async_playwright() as p:
        ctx = await _launch_context(p)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://www.bilibili.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        items = await page.evaluate(r"""() => {
          const found = new Map();
          for (const a of document.querySelectorAll('a[href*="/video/BV"]')) {
            const m = a.href.match(/(BV[0-9A-Za-z]+)/);
            if (!m) continue;
            const title = (a.getAttribute('title') || a.innerText || '').trim().replace(/\s+/g,' ');
            if (!title || /^[\d\s.,万亿:]+$/.test(title)) continue;
            if (!found.has(m[1]) || title.length > found.get(m[1]).title.length)
              found.set(m[1], {bvid:m[1], title, url:'https://www.bilibili.com/video/'+m[1]+'/'});
          }
          return Array.from(found.values());
        }""")
        await ctx.close()
    return items[:limit]

async def read_video(url):
    async with async_playwright() as p:
        ctx = await _launch_context(p)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3500)
        data = await page.evaluate("""() => ({
          title: document.querySelector('h1')?.innerText || document.title,
          description: document.querySelector('.basic-desc-info')?.innerText || ''
        })""")
        await ctx.close()
    return data

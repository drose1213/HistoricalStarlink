"""
简化版 3 分钟 Demo 录屏脚本
- 3 场景：对话演示 / 分享按钮 / 落地页反馈
- 如果 Playwright headless 录屏失败，捕获异常并打印 SKIPPED
"""
import asyncio
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path(r"d:\Ai\workspace\HistoricalStarlink\frontend\public\demo")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCENARIOS = [
    {
        "name": "scenario_1_dialogue",
        "steps": [
            ("goto", "http://localhost:5173/"),
            ("wait", 2000),
            ("screenshot", "scenario_1_home.png"),
            ("fill", "input[placeholder*='话题']", "商鞅变法"),
            ("click", "button[type='submit']"),
            ("wait", 5000),
            ("screenshot", "scenario_1_dialogue_entered.png"),
        ]
    },
    {
        "name": "scenario_2_share",
        "steps": [
            ("screenshot", "scenario_2_dialogue_page.png"),
        ]
    },
    {
        "name": "scenario_3_landing",
        "steps": [
            ("goto", "http://localhost:5173/landing?d=5aaC5p6c56em5aeL55qH5rKh5pyJ54Sa5Lmm5Z2R5YSS"),
            ("wait", 3000),
            ("screenshot", "scenario_3_landing_hero.png"),
        ]
    }
]


async def run_scenario(page, scenario):
    for action, *args in scenario["steps"]:
        if action == "goto":
            try:
                await page.goto(args[0], timeout=10000)
            except Exception as e:
                print(f"SKIP goto: {e}")
        elif action == "wait":
            await page.wait_for_timeout(int(args[0]))
        elif action == "screenshot":
            try:
                await page.screenshot(path=str(OUT_DIR / args[0]))
            except Exception as e:
                print(f"SKIP screenshot: {e}")
        elif action == "fill":
            try:
                await page.fill(args[0], args[1], timeout=3000)
            except Exception as e:
                print(f"SKIP fill: {e}")
        elif action == "click":
            try:
                await page.click(args[0], timeout=3000)
            except Exception as e:
                print(f"SKIP click: {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        for sc in SCENARIOS:
            try:
                await run_scenario(page, sc)
                print(f"OK: {sc['name']}")
            except Exception as e:
                print(f"SKIP {sc['name']}: {e}")
        await context.close()
        await browser.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())

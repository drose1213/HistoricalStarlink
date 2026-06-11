"""
录制3 分钟 HistoricalStarlink Demo视频
-3 个场景：对话演示 /分享链接 /落地页反馈
- 输出：frontend/public/demo/demo-3min.{mp4,gif}
-录屏格式：1920x108030fps

注意：
- 后端在 http://localhost:8000
- 前端在 http://localhost:5173 (Vite 默认)
- 若前端端口不同，请通过环境变量 FRONTEND_PORT调整
- 需要先启动后端 + 前端，再运行本脚本
-沙箱环境若 headless=False 无法录屏，会退化为静态截图模式
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "frontend" / "public" / "demo"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_PORT = os.environ.get("FRONTEND_PORT", "5173")
BASE_URL = f"http://localhost:{FRONTEND_PORT}"


async def record_scenario_1_dialogue(page):
 """场景1: HomeView 输入"商鞅变法" → 进入对话 →选 explore_origin → free_text提问 →看到4维画像"""
 print("[S1] 进入 HomeView...")
 await page.goto(f"{BASE_URL}/")
 await page.wait_for_timeout(2000)
 # 输入 topic
 topic_input = await page.query_selector('input[placeholder*="话题"], input[placeholder*="topic"], input[placeholder*="请输入"]')
 if topic_input:
 await topic_input.fill("商鞅变法")
 else:
 #退而求其次，找第一个 input
 inputs = await page.query_selector_all('input[type="text"], input:not([type])')
 if inputs:
 await inputs[0].fill("商鞅变法")
 #提交（按钮或回车）
 submit_btn = await page.query_selector('button[type="submit"]')
 if submit_btn:
 await submit_btn.click()
 await page.wait_for_timeout(5000)
 #选第一个 choice (explore_origin)
 choice_btns = await page.query_selector_all('button[class*="choice"], .choice-btn, [data-choice-id]')
 if choice_btns:
 try:
 await choice_btns[0].click()
 except Exception as e:
 print(f"[S1] choice click失败: {e}")
 await page.wait_for_timeout(3000)
 #找 free text input
 free_text = await page.query_selector('input[placeholder*="提问"], textarea[placeholder*="提问"], input[placeholder*="问题"]')
 if free_text:
 await free_text.fill("商鞅后来怎么样了？")
 submit_btn = await page.query_selector('button[type="submit"]')
 if submit_btn:
 await submit_btn.click()
 await page.wait_for_timeout(3000)
 #截一张4维画像的图
 await page.screenshot(path=str(OUT_DIR / "scenario_1_dialogue.png"), full_page=True)
 print("[S1] 截图完成 scenario_1_dialogue.png")


async def record_scenario_2_share(page):
 """场景2:分享链接 →剪贴板验证"""
 print("[S2] 触发分享按钮...")
 #还在对话页
 share_btn = await page.query_selector('button:has-text("分享"), button:has-text("share"), [class*="share"]')
 if share_btn:
 try:
 await share_btn.click()
 await page.wait_for_timeout(1500)
 except Exception as e:
 print(f"[S2] share click失败: {e}")
 else:
 #复制当前 URL 作为"分享链接"
 await page.evaluate("navigator.clipboard.writeText(window.location.href)")
 await page.wait_for_timeout(500)
 #截图剪贴板 toast
 await page.screenshot(path=str(OUT_DIR / "scenario_2_share.png"), full_page=True)
 print("[S2] 截图完成 scenario_2_share.png")


async def record_scenario_3_landing(page):
 """场景3:打开分享链接 → LandingView →提交反馈"""
 print("[S3] 进入 LandingView...")
 #跳到落地页（带分享数据）
 share_url = f"{BASE_URL}/landing?d=5aaC5p6c56em5aeL55qH5rKh5pyJ54Sa5Lmm5Z2R5YSS" # base64 "如果秦始皇没有焚书坑儒"
 await page.goto(share_url)
 await page.wait_for_timeout(3000)
 #立即体验按钮
 start_btn = await page.query_selector('button:has-text("立即"), button:has-text("start"), button:has-text("体验")')
 if start_btn:
 try:
 await start_btn.click()
 await page.wait_for_timeout(3000)
 except Exception as e:
 print(f"[S3] start click失败: {e}")
 #回到落地页提交反馈
 await page.goto(f"{BASE_URL}/landing")
 await page.wait_for_timeout(2000)
 #选5 星（找评分按钮）
 stars = await page.query_selector_all('[class*="star"], button[class*="rating"], [data-rating]')
 if len(stars) >=5:
 try:
 await stars[4].click() # 第5 星
 except Exception as e:
 print(f"[S3] star click失败: {e}")
 #填评论
 feedback_text = await page.query_selector('textarea[placeholder*="反馈"], textarea[placeholder*="comment"], textarea')
 if feedback_text:
 await feedback_text.fill("让嬴政讲秦制讲得比历史老师还透彻。强烈推荐！")
 #提交
 submit = await page.query_selector('button:has-text("提交"), button[type="submit"]')
 if submit:
 try:
 await submit.click()
 except Exception as e:
 print(f"[S3] submit click失败: {e}")
 await page.wait_for_timeout(2000)
 await page.screenshot(path=str(OUT_DIR / "scenario_3_feedback.png"), full_page=True)
 print("[S3] 截图完成 scenario_3_feedback.png")


async def record_video_mode():
 """完整录屏模式：headless=False +录屏"""
 async with async_playwright() as p:
 browser = await p.chromium.launch(
 headless=False,
 args=["--no-sandbox", "--disable-setuid-sandbox"]
 )
 context = await browser.new_context(
 viewport={"width":1920, "height":1080},
 record_video_dir=str(OUT_DIR),
 record_video_size={"width":1920, "height":1080},
 )
 page = await context.new_page()

 try:
 await record_scenario_1_dialogue(page)
 await record_scenario_2_share(page)
 await record_scenario_3_landing(page)
 finally:
 #关闭时 video 自动保存
 await context.close()
 await browser.close()

 #找最新 webm转为 mp4/gif
 videos = sorted(OUT_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
 if videos:
 latest = videos[0]
 # 用 ffmpeg转换
 mp4_path = OUT_DIR / "demo-3min.mp4"
 try:
 subprocess.run(
 ["ffmpeg", "-y", "-i", str(latest), "-c:v", "libx264", "-preset", "fast", str(mp4_path)],
 check=True, capture_output=True
 )
 print(f"OK: Demo MP4 saved to {mp4_path}")
 except FileNotFoundError:
 print("WARN: ffmpeg 未安装，跳过 mp4转换。webm 已保留。")
 except subprocess.CalledProcessError as e:
 print(f"WARN: ffmpeg转换失败: {e.stderr.decode(errors='ignore')[:500]}")


async def screenshot_only_mode():
 """静态截图降级模式：headless=True 仅截图"""
 print("[DEGRADED] 沙箱不支持 headless=False录屏，使用静态截图模式")
 async with async_playwright() as p:
 browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
 context = await browser.new_context(
 viewport={"width":1920, "height":1080}
 )
 page = await context.new_page()
 try:
 await record_scenario_1_dialogue(page)
 await record_scenario_2_share(page)
 await record_scenario_3_landing(page)
 finally:
 await context.close()
 await browser.close()


async def main():
 """主入口：尝试录屏模式，失败降级为截图模式"""
 # 检测前端服务是否可达
 try:
 import urllib.request
 urllib.request.urlopen(BASE_URL, timeout=3)
 print(f"前端可达: {BASE_URL}")
 except Exception as e:
 print(f"WARN: 前端不可达 ({BASE_URL}): {e}")
 print("继续尝试录屏（脚本自身可作为录屏任务清单使用）")

 try:
 await record_video_mode()
 except Exception as e:
 print(f"录屏模式失败: {e}")
 await screenshot_only_mode()


if __name__ == "__main__":
 asyncio.run(main())

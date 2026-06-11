# HistoricalStarlink 14 天投流物料

## 🎬 Demo 视频（3 分钟）
**入口**: frontend/public/demo/demo-3min.{mp4,gif}（**若未生成，参见下方"截图集"**）

## 📸 截图集（兜底）
7 张 LandingView 截图 + 3 张对话场景截图：
- landing_01_hero.png
- landing_02_features.png
- landing_03_feedback_empty.png
- landing_04_feedback_filled.png
- landing_05_feedback_submitted.png
- landing_06_full_page.png
- landing_07_hero_with_topic.png
- scenario_1_dialogue_entered.png（**如已生成**）
- scenario_3_landing_hero.png（**如已生成**）

## 📱 渠道发布物料

### 小红书版（首推）
**主标题**: "用 AI 让嬴政教你学秦制｜免费历史对话体验"
**副标题**: "4 维画像 + 因果星链，像穿越一样学历史"
**正文**: 各位历史控！发现一个神仙 APP：输入"商鞅变法"或"秦统一"，AI 嬴政/张骞直接给你演 4 维画像 + 因果星链！比 B 站纪录片有趣，比 ChatGPT 有剧情。重点是：**完全免费** → 链接见评论
**引导图**: landing_01_hero.png
**话题**: #AI 历史 #穿越式学习 #历史启蒙
**链接**: http://<your-domain>/landing

### 微博版
**主标题**: "✅ 知识型 AI 角色新品 HistoricalStarlink"
**副标题**: "让嬴政、张骞、华盛顿做你的历史家教｜免费体验"
**正文**: 厌倦了 ChatGPT 没人设？厌倦了历史游戏没知识？HistoricalStarlink 把"AI 角色 × 真实历史剧本 × 4 维画像 × 因果星链"四件套做齐。**让嬴政教你学秦制**——免费体验链接见评论
**话题**: #AI历史 #ChatGPT #历史游戏
**配图**: landing_02_features.png

### B 站版
**标题**: "让 AI 嬴政教我学秦制，比历史老师还透彻！"
**封面**: landing_06_full_page.png (3 屏拼图)
**简介**: 
- 这是一款基于 AI 的历史探索 APP
- 输入任何话题 → RAG 实时生成深度历史脉络
- 4 维画像：改革/保守/共情/激进
- 因果星链：事件之间可视化连接
- **完全免费** → 落地页链接：xxx
**标签**: AI 历史, 嬴政, 秦朝, ChatGPT, 教育科技, 因果星链

## 🖼 备选 Demo GIF 制作（若 ffmpeg 可用）
```bash
ffmpeg -i demo-3min.mp4 -vf "fps=15,scale=600:-1" -loop 0 demo-3min.gif
```
**注**: 若沙箱无 ffmpeg，**用 PNG 截图集替代 GIF**

## 📞 反馈通道
- 落地页 `/landing` 反馈表单
- 微信公众号（**待 founder 注册**）
- 邮箱: feedback@historicalstarlink.com（**待注册**）

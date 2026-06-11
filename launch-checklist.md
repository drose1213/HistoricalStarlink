# 14 天 MVP 投流发布清单

## 投流发布前 5 件事
- [ ] 后端部署到公网（Vercel/Railway/Fly.io）
- [ ] 前端 build + 部署（Vercel/Netlify/Cloudflare Pages）
- [ ] 落地页 URL 替换（mvp-14day-results.md 里的 `<domain>`）
- [ ] Demo 视频上传到 B 站 / 腾讯视频
- [ ] 3 个渠道账号准备就绪（小红书/微博/B 站）

## 渠道发布排期

### Day 13 (发布日)
- [ ] 小红书: 1 篇笔记发布
- [ ] B 站: 1 个短视频发布
- [ ] 微博: 1 条动态发布

### Day 14 (数据日)
- [ ] 调 GET /api/analytics/summary
- [ ] 填入 mvp-14day-results.md
- [ ] 决定下一步行动

## 风险预案
- **RAG 失败**: keyword fallback 已就绪，对话仍能完成
- **RAG 成本失控**: 用 `?analytics=off` 演示
- **MiniMax 反向碾压**: 抢"AI 知识型角色"品类心智第一
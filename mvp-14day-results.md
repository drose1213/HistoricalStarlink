# HistoricalStarlink 14 天 MVP 首份 PMF 基线报告

> **生成日期**: 2026-06-09
> **报告周期**: Day 1 - Day 14
> **北极星目标**: 100 种子用户 + ARPU 49 元/月 + 7 日留存 35%
> **状态**: 进行中 / 已达成 / 未达成

---

## 一、核心指标（来自 GET /api/analytics/summary）

| 指标 | 实际值 | 目标值 | 达成度 |
|------|--------|--------|--------|
| 总埋点数 | <从 summary 取> | - | - |
| 唯一用户数（按 UA 去重） | <从 summary 取> | 100 | <%> |
| `app_enter` 事件 | <从 summary 取> | ≥ 100 | - |
| `dialogue_completed` 事件 | <从 summary 取> | ≥ 30 | - |
| `paywall_clicked` 事件 | <从 summary 取> | ≥ 10 | - |
| `feedback_submitted` 事件 | <从 summary 取> | ≥ 20 | - |
| 平均反馈评分 | <从 summary 取> | ≥ 4.0 | - |
| 平均对话时长（秒） | <从 summary 取> | - | - |

## 二、Top 10 热门话题

| 排名 | 话题 | 完成次数 |
|------|------|----------|
| 1 | <topic> | <count> |
| 2 | ... | ... |

## 三、用户行为漏斗

```
app_enter (X) → dialogue_completed (Y) → paywall_clicked (Z) → feedback_submitted (W)
转化率：app_enter → dialogue_completed = Y/X
       dialogue_completed → paywall_clicked = Z/Y
       paywall_clicked → feedback_submitted = W/Z
```

## 四、付费意愿验证（核心非共识判断）

- **`paywall_clicked` 事件数 = <Z>** —— 关键指标
- **与星野基线对比**: 星野平均点击率为 8-12%
- **我们做到了 <Z/Y> 倍** —— 1.5x 算超预期，<1x 算失败

**结论判定**:
- ✅ **非共识成立** (ARPU 可达 49 元/月): paywall_clicked 转化 ≥ 星野基线 1.5x
- ⚠️ **待验证**: paywall_clicked 转化 = 星野基线 1-1.5x
- ❌ **非共识证伪** (ARPU 跌回 19 元/月): paywall_clicked 转化 < 星野基线

## 五、100 种子用户名单（Day 1-14 收集）

| 序号 | 用户标识（UA hash） | 首次进入时间 | 反馈评分 | 备注 |
|------|---------------------|--------------|----------|------|
| 1 | <hash> | <ts> | - | - |
| ... | ... | ... | ... | ... |

## 六、关键发现 & 下一步

### 发现
- <如：Z 世代偏好"商鞅变法"等争议性话题，付费意愿更高>
- <如：对话时长 80-120s 是甜点>

### 下一步
- **若非共识成立**: 启动 A 轮融资，目标 3000-5000 万人民币
- **若非共识待验证**: 跑 A/B 测试优化 paywall 触发位置
- **若非共识证伪**: 转向 Pop Mart 卡牌情感经济路径

---

## 附录

### 附 A: 完整 summary JSON

```json
<从 GET /api/analytics/summary 取的实际 JSON>
```

### 附 B: Demo 物料链接
- 3 分钟 Demo 录屏: frontend/public/demo/demo-3min.mp4
- 落地页: http://<domain>/landing
- LandingView 截图: frontend/landing_screenshots/

### 附 C: 投流渠道数据
- 小红书 1 篇笔记
- B 站 1 个短视频
- 微博 1 条动态
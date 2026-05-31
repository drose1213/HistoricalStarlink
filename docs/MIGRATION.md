# 历史星链探索 - App跨平台迁移指南

## 项目结构

```
hitstorygame/
├── index.html              # Web版入口
├── components/
│   └── HistoryStarlink.vue # Vue 3 组件（核心，可跨平台）
├── scripts/
│   ├── data.js            # 历史数据
│   ├── chart.js           # 柱状图模块
│   ├── starlink.js        # 星链视图模块
│   └── app.js            # Web版主入口
├── styles/
│   └── main.css          # 样式
└── docs/
    └── specs/             # 设计文档
```

## 跨平台方案

### 方案一：uni-app（推荐）

uni-app 是最简洁的跨平台方案，一套代码可编译到：
- iOS App
- Android App
- H5
- 微信/支付宝/抖音小程序
- 各种小程序

**迁移步骤：**

```bash
# 1. 创建uni-app项目
npx degit dcloudio/uni-preset-vue#vite my-history-app
cd my-history-app

# 2. 复制组件
cp -r hitstorygame/components/HistoryStarlink.vue src/components/
cp -r hitstorygame/scripts/data.js src/utils/

# 3. 修改组件适配uni-app
# 主要调整：
# - 移除原生canvas，改用uni-app的canvas组件或ucharts
# - SVG改用view组件实现
# - 触摸事件适配
```

**关键适配点：**

```vue
<!-- uni-app版本示例 -->
<template>
  <view class="history-starlink">
    <!-- 图表用ucharts或canvas -->
    <canvas 
      canvas-id="historyChart" 
      @touchstart="handleTouch"
    ></canvas>
    
    <!-- 星链图用view实现 -->
    <view class="starlink-nodes">
      <view 
        v-for="node in nodes" 
        :key="node.id"
        class="node"
        :style="getNodeStyle(node)"
        @tap="onNodeTap(node)"
      >
        {{ node.name }}
      </view>
    </view>
  </view>
</template>

<script>
import { HISTORY_DATA, DataUtils } from '@/utils/data.js'

export default {
  components: { HistoryStarlink },
  // ... 核心逻辑复用
}
</script>
```

### 方案二：Taro

Taro 同样支持多端，React生态。

```bash
# 创建Taro项目
npx create@tarojs/taro@latest my-history-app

# 复制组件，React版本重写
```

### 方案三：React Native

如需原生体验，可手动适配RN：

- Canvas → react-native-svg 或 react-native-canvas
- 动画 → react-native-reanimated
- 手势 → react-native-gesture-handler

---

## 数据层扩展（RAG知识库）

后续接RAG时，只需替换 `data.js` 的数据源：

```javascript
// 替换前（静态数据）
const HISTORY_DATA = { events: [...] }

// 替换后（RAG API）
async function queryHistory(query) {
  const response = await fetch('/api/rag/query', {
    method: 'POST',
    body: JSON.stringify({ query })
  });
  return response.json();
}

// 保持接口不变
const DataUtils = {
  getEventById: (id) => queryHistory(`事件 ${id} 的详情`),
  getRelatedEvents: (id) => queryHistory(`${id} 的前因后果`)
  // ...
}
```

---

## App功能清单

| 功能 | Web | 小程序 | App |
|------|-----|--------|-----|
| 柱状图浏览 | ✅ | ✅ | ✅ |
| 事件筛选 | ✅ | ✅ | ✅ |
| 星链探索 | ✅ | ✅ | ✅ |
| 探索历史 | ✅ | ✅ | ✅ |
| RAG知识库 | 待开发 | 待开发 | 待开发 |
| 角色扮演 | 待开发 | 待开发 | 待开发 |
| 旅程存档 | LocalStorage | Storage | Storage/云端 |

---

## 快速启动

```bash
# Web预览
cd hitstorygame
npx serve .

# 或直接用浏览器打开 index.html
```

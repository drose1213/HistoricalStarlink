<template>
  <div class="history-starlink hs-dark">
    <!-- Header -->
    <header class="hs-header">
      <div class="hs-logo">
        <span class="hs-logo-icon">◇</span>
        <h1 class="hs-title">历史星链探索</h1>
      </div>
      <nav class="hs-filter">
        <button
          v-for="f in filters"
          :key="f.value"
          class="hs-filter-btn"
          :class="{ active: currentFilter === f.value }"
          @click="setFilter(f.value)"
        >
          {{ f.label }}
        </button>
      </nav>
    </header>

    <!-- Chart View - 3D Core -->
    <section v-show="currentView === 'chart'" class="hs-view hs-chart-view">
      <div class="hs-chart-wrapper">
        <!-- 左侧东方事件 -->
        <div class="hs-side left">
          <div
            v-for="(event, i) in leftEvents"
            :key="event.id"
            class="hs-event-marker"
            :style="{ top: getPosition(event) + '%', '--color': '#00f5ff' }"
            @click="navigateTo(event)"
          >
            <span class="hs-event-year">{{ formatYear(event.year) }}</span>
            <span class="hs-event-name">{{ event.name }}</span>
            <span class="hs-event-dot"></span>
          </div>
        </div>

        <!-- 中央3D岩芯 -->
        <div class="hs-core-container">
          <div class="hs-core">
            <div class="hs-core-top">
              <div class="hs-core-surface"></div>
            </div>
            <div class="hs-core-body">
              <div
                v-for="(layer, i) in earthLayers"
                :key="i"
                class="hs-layer"
                :style="{ background: layer }"
              ></div>
              <!-- 核心标记点 -->
              <div
                v-for="event in filteredEvents"
                :key="event.id"
                class="hs-marker"
                :class="event.region"
                :style="{ top: getPosition(event) + '%' }"
                :title="event.name"
                @click="navigateTo(event)"
              ></div>
            </div>
            <div class="hs-core-bottom"></div>
          </div>
        </div>

        <!-- 右侧西方事件 -->
        <div class="hs-side right">
          <div
            v-for="(event, i) in rightEvents"
            :key="event.id"
            class="hs-event-marker right"
            :style="{ top: getPosition(event) + '%', '--color': '#ff00ff' }"
            @click="navigateTo(event)"
          >
            <span class="hs-event-dot"></span>
            <span class="hs-event-name">{{ event.name }}</span>
            <span class="hs-event-year">{{ formatYear(event.year) }}</span>
          </div>
        </div>
      </div>

      <!-- 时间轴 -->
      <div class="hs-timeline">
        <span>-3000 BCE</span>
        <span>-2000</span>
        <span>-1000</span>
        <span>0</span>
        <span>1000</span>
        <span>2000 CE</span>
      </div>
    </section>

    <!-- Starlink View -->
    <section v-show="currentView === 'starlink'" class="hs-view hs-starlink-view">
      <div class="hs-starlink-header">
        <button class="hs-back-btn" @click="goToChart">
          <span>←</span> 返回
        </button>
        <div class="hs-breadcrumb">
          <span
            v-for="(event, index) in exploreHistory"
            :key="index"
            class="hs-breadcrumb-item"
            @click="jumpToHistory(index)"
          >
            {{ event.name }} <span class="sep">›</span>
          </span>
        </div>
      </div>
      <div class="hs-starlink-content">
        <svg ref="starlinkSvg" class="hs-starlink-svg"></svg>
        <div class="hs-event-detail" v-if="currentEvent">
          <h2 class="hs-detail-title">{{ currentEvent.name }}</h2>
          <div class="hs-detail-meta">
            <span>{{ formatYear(currentEvent.year) }}</span>
            <span>{{ currentEvent.region === 'china' ? '东方' : '西方' }}</span>
          </div>
          <p class="hs-detail-desc">{{ currentEvent.description }}</p>
          <div class="hs-detail-section" v-if="causeEvents.length">
            <h3>↖ 前因</h3>
            <ul>
              <li v-for="e in causeEvents" :key="e.id" @click="navigateTo(e)">{{ e.name }}</li>
            </ul>
          </div>
          <div class="hs-detail-section" v-if="effectEvents.length">
            <h3>↘ 影响</h3>
            <ul>
              <li v-for="e in effectEvents" :key="e.id" @click="navigateTo(e)">{{ e.name }}</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { HISTORY_DATA, DataUtils } from './data.js';

/**
 * HistoryStarlink - Vue 3 跨平台组件 (3D岩芯版)
 * 兼容: Web / 微信小程序 / App (uni-app / Taro)
 */
export default {
  name: 'HistoryStarlink',

  props: {
    initialFilter: {
      type: String,
      default: 'all'
    },
    initialEvent: {
      type: String,
      default: null
    }
  },

  data() {
    return {
      filters: [
        { label: '全部', value: 'all' },
        { label: '东方', value: 'china' },
        { label: '西方', value: 'foreign' }
      ],
      currentFilter: 'all',
      currentView: 'chart',
      currentEvent: null,
      exploreHistory: [],
      earthLayers: [
        'rgba(0, 245, 255, 0.1)',
        'rgba(157, 78, 221, 0.15)',
        'rgba(255, 0, 255, 0.1)',
        'rgba(0, 245, 255, 0.12)',
        'rgba(157, 78, 221, 0.18)',
        'rgba(255, 0, 255, 0.08)',
        'rgba(0, 245, 255, 0.1)',
        'rgba(157, 78, 221, 0.15)',
        'rgba(255, 0, 255, 0.1)',
        'rgba(0, 245, 255, 0.12)',
        'rgba(157, 78, 221, 0.18)',
        'rgba(255, 0, 255, 0.08)'
      ]
    };
  },

  computed: {
    filteredEvents() {
      return DataUtils.filterByRegion(this.currentFilter);
    },

    leftEvents() {
      return this.filteredEvents
        .filter(e => e.region === 'china')
        .slice(0, 8);
    },

    rightEvents() {
      return this.filteredEvents
        .filter(e => e.region === 'foreign')
        .slice(0, 8);
    },

    causeEvents() {
      if (!this.currentEvent) return [];
      return DataUtils.getRelatedEvents(this.currentEvent.id).causes;
    },

    effectEvents() {
      if (!this.currentEvent) return [];
      return DataUtils.getRelatedEvents(this.currentEvent.id).consequences;
    }
  },

  methods: {
    setFilter(filter) {
      this.currentFilter = filter;
    },

    formatYear(year) {
      return year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
    },

    getPosition(event) {
      const range = DataUtils.getYearRange();
      return ((event.year - range.min) / (range.max - range.min)) * 100;
    },

    navigateTo(event) {
      this.currentEvent = event;
      this.exploreHistory.push(event);
      this.currentView = 'starlink';
      this.$emit('event-change', event);
      this.$nextTick(() => {
        this.renderStarlink();
      });
    },

    goToChart() {
      this.currentView = 'chart';
      this.exploreHistory = [];
      this.currentEvent = null;
    },

    jumpToHistory(index) {
      if (index < 0) {
        this.goToChart();
        return;
      }
      const event = this.exploreHistory[index];
      this.exploreHistory = this.exploreHistory.slice(0, index + 1);
      this.navigateTo(event);
    },

    renderStarlink() {
      const svg = this.$refs.starlinkSvg;
      if (!svg || !this.currentEvent) return;

      const rect = svg.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      svg.innerHTML = '';

      // 背景
      const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      bg.setAttribute('width', '100%');
      bg.setAttribute('height', '100%');
      bg.setAttribute('fill', '#0a0a0f');
      svg.appendChild(bg);

      // 中心节点
      const centerNode = this.createNode(
        this.currentEvent.id,
        this.currentEvent.name,
        this.currentEvent.region,
        centerX,
        centerY,
        35,
        true
      );
      svg.appendChild(centerNode);

      // 关联节点
      const related = DataUtils.getRelatedEvents(this.currentEvent.id);
      const causes = related.causes.slice(0, 5);
      const effects = related.consequences.slice(0, 5);

      causes.forEach((event, i) => {
        const angle = -Math.PI / 2 + (i - (causes.length - 1) / 2) * 0.3;
        const x = centerX + Math.cos(angle) * 120;
        const y = centerY + Math.sin(angle) * 120;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x); line.setAttribute('y1', y);
        line.setAttribute('x2', centerX); line.setAttribute('y2', centerY);
        line.setAttribute('stroke', '#00f5ff');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-dasharray', '5,5');
        svg.appendChild(line);

        const node = this.createNode(event.id, event.name, event.region, x, y, 22, false);
        svg.appendChild(node);
      });

      effects.forEach((event, i) => {
        const angle = Math.PI / 2 + (i - (effects.length - 1) / 2) * 0.3;
        const x = centerX + Math.cos(angle) * 120;
        const y = centerY + Math.sin(angle) * 120;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', centerX); line.setAttribute('y1', centerY);
        line.setAttribute('x2', x); line.setAttribute('y2', y);
        line.setAttribute('stroke', '#ff00ff');
        line.setAttribute('stroke-width', '2');
        svg.appendChild(line);

        const node = this.createNode(event.id, event.name, event.region, x, y, 22, false);
        svg.appendChild(node);
      });
    },

    createNode(id, name, region, x, y, radius, isCenter) {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('data-id', id);
      g.style.cursor = 'pointer';

      const color = region === 'china' ? '#00f5ff' : '#ff00ff';

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', x);
      circle.setAttribute('cy', y);
      circle.setAttribute('r', radius);
      circle.setAttribute('fill', isCenter ? '#00f5ff' : color);
      circle.setAttribute('stroke', isCenter ? 'white' : color);
      circle.setAttribute('stroke-width', '2');
      g.appendChild(circle);

      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', x);
      text.setAttribute('y', y + radius + 18);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('fill', '#e0e0e0');
      text.setAttribute('font-size', '12');
      text.textContent = name;
      g.appendChild(text);

      g.addEventListener('click', () => {
        const event = DataUtils.getEventById(id);
        if (event && !isCenter) {
          this.navigateTo(event);
        }
      });

      return g;
    }
  }
};
</script>

<style scoped>
/* ========================================
   历史星链探索 - 3D岩芯风格组件样式
   ======================================== */

.history-starlink {
  width: 100%;
  height: 100vh;
  background: #0a0a0f;
  color: #e0e0e0;
  font-family: 'Noto Sans SC', sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.hs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(180deg, #12121a, transparent);
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
  z-index: 10;
}

.hs-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hs-logo-icon {
  font-size: 24px;
  color: #00f5ff;
  text-shadow: 0 0 20px #00f5ff;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.hs-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(90deg, #00f5ff, #ff00ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hs-filter {
  display: flex;
  gap: 8px;
}

.hs-filter-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 4px;
  color: #888;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.hs-filter-btn.active {
  background: #00f5ff;
  color: #0a0a0f;
  font-weight: 600;
}

/* Chart View */
.hs-chart-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.hs-chart-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 800px;
}

/* 两侧事件 */
.hs-side {
  width: 30%;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 40px 20px;
}

.hs-side.left {
  align-items: flex-end;
}

.hs-side.right {
  align-items: flex-start;
}

.hs-event-marker {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(26, 26, 46, 0.9);
  border: 1px solid var(--color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.hs-event-marker:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px var(--color);
}

.hs-event-marker.right {
  flex-direction: row-reverse;
}

.hs-event-year {
  font-size: 11px;
  color: #888;
  font-family: monospace;
}

.hs-event-name {
  font-size: 13px;
  color: #e0e0e0;
  white-space: nowrap;
}

.hs-event-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color);
  box-shadow: 0 0 8px var(--color);
}

/* 中央3D岩芯 */
.hs-core-container {
  width: 160px;
  height: 80%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hs-core {
  width: 80px;
  height: 100%;
  position: relative;
}

.hs-core-top {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3d5c3d, #2d4a2d, #1a2f1a);
  border: 2px solid #4a6b4a;
  box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
}

.hs-core-surface {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60%;
  height: 60%;
  border-radius: 50%;
  background: radial-gradient(ellipse at 30% 30%, rgba(255,255,255,0.2), transparent);
}

.hs-core-body {
  position: absolute;
  top: 35px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: calc(100% - 35px);
  border-radius: 0 0 40px 40px;
  overflow: hidden;
  box-shadow:
    inset -10px 0 20px rgba(0,0,0,0.5),
    inset 10px 0 20px rgba(255,255,255,0.05);
}

.hs-layer {
  width: 100%;
  height: 8.33%;
  border-bottom: 1px solid rgba(0,0,0,0.2);
}

.hs-marker {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid rgba(255,255,255,0.5);
  transition: all 0.2s;
  z-index: 10;
}

.hs-marker:hover {
  transform: translateX(-50%) scale(1.5);
  z-index: 100;
}

.hs-marker.china {
  background: #00f5ff;
  box-shadow: 0 0 10px #00f5ff;
}

.hs-marker.foreign {
  background: #ff00ff;
  box-shadow: 0 0 10px #ff00ff;
}

.hs-core-bottom {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 15px;
  border-radius: 0 0 40px 40px;
  background: linear-gradient(180deg, #1a0f0a, #0a0505);
}

/* 时间轴 */
.hs-timeline {
  display: flex;
  justify-content: space-between;
  padding: 15px 20% 10px;
  font-size: 12px;
  color: #888;
  font-family: monospace;
  border-top: 1px solid rgba(0, 245, 255, 0.2);
}

.hs-timeline span {
  position: relative;
}

.hs-timeline span::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 6px;
  background: #00f5ff;
}

/* Starlink View */
.hs-starlink-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.hs-starlink-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: #12121a;
  border-bottom: 1px solid rgba(0, 245, 255, 0.3);
}

.hs-back-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #ff00ff;
  border-radius: 4px;
  color: #ff00ff;
  cursor: pointer;
}

.hs-breadcrumb {
  font-size: 13px;
  color: #888;
  overflow-x: auto;
}

.hs-breadcrumb-item {
  color: #00f5ff;
  cursor: pointer;
}

.sep {
  margin: 0 8px;
  color: #888;
}

.hs-starlink-content {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.hs-starlink-svg {
  width: 100%;
  height: 60%;
}

.hs-event-detail {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 600px;
  padding: 24px;
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
}

.hs-detail-title {
  font-size: 20px;
  color: #00f5ff;
  margin-bottom: 8px;
}

.hs-detail-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
}

.hs-detail-desc {
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 16px;
}

.hs-detail-section h3 {
  font-size: 13px;
  color: #ff00ff;
  margin-bottom: 8px;
}

.hs-detail-section ul {
  list-style: none;
}

.hs-detail-section li {
  padding: 6px 0;
  color: #888;
  cursor: pointer;
}

.hs-detail-section li:hover {
  color: #00f5ff;
}

/* Responsive */
@media (max-width: 768px) {
  .hs-header {
    flex-direction: column;
    gap: 12px;
  }

  .hs-chart-wrapper {
    flex-direction: column;
  }

  .hs-side {
    width: 100%;
    height: auto;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    padding: 10px;
  }

  .hs-event-marker {
    position: relative;
    margin: 4px;
  }

  .hs-core-container {
    width: 100%;
    height: 200px;
  }
}
</style>

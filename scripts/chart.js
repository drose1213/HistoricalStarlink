/**
 * 历史星链探索 - 柱状图模块
 */

class HistoryChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.tooltip = document.getElementById('tooltip');
    this.events = [];
    this.filter = 'all';
    this.padding = { top: 60, right: 60, bottom: 80, left: 80 };
    this.barGap = 40;
    this.currentFilter = 'all';

    this.colors = {
      china: '#ffd700',
      foreign: '#00f5ff',
      axis: 'rgba(0, 245, 255, 0.3)',
      text: '#e0e0e0',
      textSecondary: '#888888',
      grid: 'rgba(0, 245, 255, 0.1)'
    };

    this.hoveredEvent = null;
    this.animationProgress = 0;
    this.isAnimating = true;

    this.init();
  }

  init() {
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    this.canvas.addEventListener('mouseleave', () => this.hideTooltip());
  }

  resize() {
    const container = this.canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    const width = container.clientWidth;
    const height = container.clientHeight;

    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.ctx.scale(dpr, dpr);

    this.width = width;
    this.height = height;
    this.chartWidth = width - this.padding.left - this.padding.right;
    this.chartHeight = height - this.padding.top - this.padding.bottom;

    this.render();
  }

  setFilter(filter) {
    this.currentFilter = filter;
    this.filter = filter;
    this.events = DataUtils.filterByRegion(filter);
    this.sortByYear();
    this.isAnimating = true;
    this.animationProgress = 0;
    this.render();
  }

  sortByYear() {
    this.events.sort((a, b) => a.year - b.year);
  }

  getBarWidth() {
    const totalBars = this.events.length;
    if (totalBars === 0) return 0;
    return Math.min(40, (this.chartWidth - (totalBars - 1) * this.barGap) / totalBars);
  }

  getXForEvent(event, index) {
    const barWidth = this.getBarWidth();
    const totalBarsWidth = this.events.length * barWidth + (this.events.length - 1) * this.barGap;
    const startX = this.padding.left + (this.chartWidth - totalBarsWidth) / 2;
    return startX + index * (barWidth + this.barGap);
  }

  getYForEvent(event) {
    const minYear = DataUtils.getYearRange().min;
    const maxYear = DataUtils.getYearRange().max;
    const yearRange = maxYear - minYear;

    const x = this.padding.left + ((event.year - minYear) / yearRange) * this.chartWidth;
    return x;
  }

  render() {
    if (this.isAnimating) {
      this.animationProgress += 0.02;
      if (this.animationProgress > 1) {
        this.animationProgress = 1;
        this.isAnimating = false;
      }
    }

    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 绘制背景网格
    this.drawGrid();

    // 绘制时间轴
    this.drawAxis();

    // 绘制柱子
    this.drawBars();

    // 绘制标签
    this.drawLabels();

    if (this.isAnimating) {
      requestAnimationFrame(() => this.render());
    }
  }

  drawGrid() {
    const ctx = this.ctx;
    const { min, max } = DataUtils.getYearRange();

    // 垂直网格线（按世纪划分）
    const centuryRange = 200;
    const startCentury = Math.ceil(min / centuryRange) * centuryRange;

    ctx.strokeStyle = this.colors.grid;
    ctx.lineWidth = 1;

    for (let year = startCentury; year <= max; year += centuryRange) {
      const x = this.getXForYear(year);
      if (x >= this.padding.left && x <= this.width - this.padding.right) {
        ctx.beginPath();
        ctx.moveTo(x, this.padding.top);
        ctx.lineTo(x, this.height - this.padding.bottom);
        ctx.stroke();
      }
    }
  }

  drawAxis() {
    const ctx = this.ctx;

    // X轴
    ctx.strokeStyle = this.colors.axis;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(this.padding.left, this.height - this.padding.bottom);
    ctx.lineTo(this.width - this.padding.right, this.height - this.padding.bottom);
    ctx.stroke();

    // Y轴（水平时间轴）
    ctx.beginPath();
    ctx.moveTo(this.padding.left, this.height - this.padding.bottom);
    ctx.lineTo(this.padding.left, this.padding.top);
    ctx.stroke();

    // 时间刻度和标签
    const { min, max } = DataUtils.getYearRange();
    const centuryRange = 500;
    const startCentury = Math.ceil(min / centuryRange) * centuryRange;

    ctx.fillStyle = this.colors.textSecondary;
    ctx.font = '12px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';

    for (let year = startCentury; year <= max; year += centuryRange) {
      const x = this.getXForYear(year);
      if (x >= this.padding.left && x <= this.width - this.padding.right) {
        // 刻度线
        ctx.strokeStyle = this.colors.axis;
        ctx.beginPath();
        ctx.moveTo(x, this.height - this.padding.bottom);
        ctx.lineTo(x, this.height - this.padding.bottom + 8);
        ctx.stroke();

        // 标签
        const label = year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
        ctx.fillText(label, x, this.height - this.padding.bottom + 24);
      }
    }

    // 轴标题
    ctx.fillStyle = this.colors.text;
    ctx.font = '14px "Noto Sans SC", sans-serif';
    ctx.fillText('时间轴 (公元前/公元后)', this.width / 2, this.height - 15);
  }

  getXForYear(year) {
    const { min, max } = DataUtils.getYearRange();
    return this.padding.left + ((year - min) / (max - min)) * this.chartWidth;
  }

  drawBars() {
    const ctx = this.ctx;
    const barWidth = this.getBarWidth();
    const maxBarHeight = this.chartHeight - 40;

    this.events.forEach((event, index) => {
      const x = this.getXForEvent(event, index);
      const normalizedImportance = event.importance / 10;
      const targetHeight = normalizedImportance * maxBarHeight;
      const barHeight = targetHeight * this.animationProgress;

      const y = this.height - this.padding.bottom - barHeight;
      const color = event.region === 'china' ? this.colors.china : this.colors.foreign;

      // 发光效果
      ctx.shadowColor = color;
      ctx.shadowBlur = this.hoveredEvent === event ? 25 : 15;

      // 渐变填充
      const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
      gradient.addColorStop(0, color);
      gradient.addColorStop(1, this.adjustColor(color, -0.3));

      ctx.fillStyle = gradient;
      ctx.fillRect(x, y, barWidth, barHeight);

      // 顶部高光
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.fillRect(x, y, barWidth, 3);

      ctx.shadowBlur = 0;
    });
  }

  drawLabels() {
    const ctx = this.ctx;
    const barWidth = this.getBarWidth();
    const labelInterval = Math.max(1, Math.floor(this.events.length / 15));

    this.events.forEach((event, index) => {
      if (index % labelInterval !== 0 && this.events.length > 10) return;

      const x = this.getXForEvent(event, index) + barWidth / 2;
      const y = this.height - this.padding.bottom + 40;
      const color = event.region === 'china' ? this.colors.china : this.colors.foreign;

      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(-Math.PI / 4);

      ctx.fillStyle = color;
      ctx.font = '11px "Noto Sans SC", sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(event.name, 0, 0);

      ctx.restore();
    });
  }

  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const barWidth = this.getBarWidth();
    let found = null;

    this.events.forEach((event, index) => {
      const barX = this.getXForEvent(event, index);
      if (x >= barX && x <= barX + barWidth && y >= this.padding.top && y <= this.height - this.padding.bottom) {
        found = event;
      }
    });

    if (found) {
      this.hoveredEvent = found;
      this.showTooltip(found, e.clientX, e.clientY);
      this.canvas.style.cursor = 'pointer';
    } else {
      this.hoveredEvent = null;
      this.hideTooltip();
      this.canvas.style.cursor = 'default';
    }

    this.render();
  }

  handleClick(e) {
    if (this.hoveredEvent) {
      this.onEventClick(this.hoveredEvent);
    }
  }

  onEventClick(event) {
    // 由外部app.js处理
    if (this.clickHandler) {
      this.clickHandler(event);
    }
  }

  showTooltip(event, mouseX, mouseY) {
    const yearText = event.year < 0 ? `${Math.abs(event.year)} BCE` : `${event.year} CE`;
    const regionText = event.region === 'china' ? '中国' : '外国';

    this.tooltip.innerHTML = `
      <div class="tooltip-title">${event.name}</div>
      <div class="tooltip-year">${yearText} · ${regionText}</div>
      <div class="tooltip-desc">${event.description.substring(0, 60)}...</div>
    `;

    this.tooltip.style.left = `${mouseX}px`;
    this.tooltip.style.top = `${mouseY}px`;
    this.tooltip.classList.remove('hidden');
  }

  hideTooltip() {
    this.tooltip.classList.add('hidden');
  }

  adjustColor(color, amount) {
    const hex = color.replace('#', '');
    const r = Math.max(0, Math.min(255, parseInt(hex.substr(0, 2), 16) + amount * 255));
    const g = Math.max(0, Math.min(255, parseInt(hex.substr(2, 2), 16) + amount * 255));
    const b = Math.max(0, Math.min(255, parseInt(hex.substr(4, 2), 16) + amount * 255));
    return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = HistoryChart;
}

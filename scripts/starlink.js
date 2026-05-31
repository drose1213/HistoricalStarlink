/**
 * 历史星链探索 - 星链视图模块
 * 当前事件居中，早于当前事件的节点在左侧，晚于当前事件的节点在右侧。
 */

class StarlinkView {
  constructor(svgId, detailId) {
    this.svg = document.getElementById(svgId);
    this.detailPanel = document.getElementById(detailId);
    this.centerEvent = null;
    this.history = [];
    this.nodes = [];
    this.links = [];

    if (!this.svg || !this.detailPanel) {
      throw new Error('StarlinkView 初始化失败：缺少 SVG 或详情容器');
    }

    this.palette = [
      '#31f7ff',
      '#ff35f3',
      '#ffd166',
      '#5dff9c',
      '#ff7a59',
      '#8f7cff',
      '#00d4ff',
      '#f7ff58',
      '#ff5fa2',
      '#74f0c7'
    ];

    this.colors = {
      center: '#ffffff',
      chinaRing: '#ff335c',
      foreignRing: '#ffd166',
      text: '#eafaff',
      muted: '#8ea4b8',
      grid: 'rgba(49, 247, 255, 0.055)'
    };

    this.config = {
      centerRadius: 38,
      nodeRadiusLarge: 26,
      nodeRadiusSmall: 21,
      sidePadding: 148,
      verticalPadding: 82,
      animationDuration: 420
    };
  }

  showEvent(event, addToHistory = true) {
    if (!event) return;

    if (addToHistory && this.centerEvent && this.centerEvent.id !== event.id) {
      this.history.push(this.centerEvent.id);
    }

    this.centerEvent = event;
    this.render(event);
    this.updateBreadcrumb();
  }

  render(event) {
    this.svg.replaceChildren();
    this.nodes = [];
    this.links = [];

    const rect = this.svg.getBoundingClientRect();
    const width = Math.max(rect.width, 1);
    const height = Math.max(rect.height, 1);
    const centerX = width / 2;
    const centerY = height * 0.42;

    this.drawBackground(width, height);

    const groups = this.getChronologicalGroups(event);
    const leftPositions = this.getSidePositions(groups.earlier.length, 'left', width, height);
    const rightPositions = this.getSidePositions(groups.later.length, 'right', width, height);

    let colorIndex = 0;
    groups.earlier.forEach((item, index) => {
      const position = leftPositions[index];
      const color = this.getNodeColor(colorIndex);
      this.drawLink(position.x, position.y, centerX, centerY, color, true, colorIndex * 55);
      this.drawNode(item.event, position.x, position.y, false, color);
      colorIndex += 1;
    });

    groups.later.forEach((item, index) => {
      const position = rightPositions[index];
      const color = this.getNodeColor(colorIndex);
      this.drawLink(centerX, centerY, position.x, position.y, color, false, colorIndex * 55);
      this.drawNode(item.event, position.x, position.y, false, color);
      colorIndex += 1;
    });

    this.drawNode(event, centerX, centerY, true, this.colors.center);
    this.showDetail(event, groups);
  }

  getChronologicalGroups(event) {
    const related = DataUtils.getRelatedEvents(event.id);
    const byId = new Map();

    [...related.causes, ...related.consequences].forEach(relatedEvent => {
      if (relatedEvent && relatedEvent.id !== event.id && !byId.has(relatedEvent.id)) {
        byId.set(relatedEvent.id, relatedEvent);
      }
    });

    const allRelated = [...byId.values()].sort((a, b) => a.year - b.year);

    return {
      earlier: allRelated
        .filter(relatedEvent => relatedEvent.year < event.year)
        .map(relatedEvent => ({ event: relatedEvent })),
      later: allRelated
        .filter(relatedEvent => relatedEvent.year >= event.year)
        .map(relatedEvent => ({ event: relatedEvent }))
    };
  }

  getSidePositions(count, side, width, height) {
    if (count <= 0) return [];

    const x = side === 'left' ? this.config.sidePadding : width - this.config.sidePadding;
    const availableHeight = Math.max(height * 0.54, 220);
    const startY = Math.max(this.config.verticalPadding, height * 0.16);
    const step = count === 1 ? 0 : availableHeight / (count - 1);

    return Array.from({ length: count }, (_, index) => ({
      x,
      y: count === 1 ? height * 0.42 : startY + step * index
    }));
  }

  getNodeColor(index) {
    return this.palette[index % this.palette.length];
  }

  drawBackground(width, height) {
    const defs = this.createSvgElement('defs');
    const gradient = this.createSvgElement('radialGradient', { id: 'bgGradient' });
    gradient.appendChild(this.createSvgElement('stop', { offset: '0%', 'stop-color': '#18253d' }));
    gradient.appendChild(this.createSvgElement('stop', { offset: '58%', 'stop-color': '#09101d' }));
    gradient.appendChild(this.createSvgElement('stop', { offset: '100%', 'stop-color': '#03060c' }));
    defs.appendChild(gradient);
    this.svg.appendChild(defs);

    this.svg.appendChild(this.createSvgElement('rect', {
      width: '100%',
      height: '100%',
      fill: 'url(#bgGradient)'
    }));

    for (let x = 0; x < width; x += 40) {
      this.svg.appendChild(this.createSvgElement('line', {
        x1: x,
        y1: 0,
        x2: x,
        y2: height,
        stroke: this.colors.grid,
        'stroke-width': 1
      }));
    }

    for (let y = 0; y < height; y += 40) {
      this.svg.appendChild(this.createSvgElement('line', {
        x1: 0,
        y1: y,
        x2: width,
        y2: y,
        stroke: this.colors.grid,
        'stroke-width': 1
      }));
    }
  }

  drawLink(x1, y1, x2, y2, color, dashed, delay) {
    const line = this.createSvgElement('line', {
      x1,
      y1,
      x2,
      y2,
      stroke: color,
      'stroke-width': 2.4,
      opacity: 0,
      filter: `drop-shadow(0 0 5px ${color})`
    });

    if (dashed) {
      line.setAttribute('stroke-dasharray', '7 5');
    }

    setTimeout(() => {
      line.style.transition = `opacity ${this.config.animationDuration}ms ease-out`;
      line.setAttribute('opacity', '0.78');
    }, delay);

    this.svg.appendChild(line);
    this.links.push(line);
  }

  drawNode(event, x, y, isCenter, color) {
    const group = this.createSvgElement('g', {
      class: isCenter ? 'starlink-node current-node' : 'starlink-node',
      'data-id': event.id,
      'data-region': event.region,
      'data-year': event.year,
      'data-center': isCenter ? 'true' : 'false'
    });
    group.style.cursor = isCenter ? 'default' : 'pointer';

    const radius = isCenter
      ? this.config.centerRadius
      : event.importance >= 8 ? this.config.nodeRadiusLarge : this.config.nodeRadiusSmall;

    const ringColor = this.getRegionRingColor(event.region);
    const regionRing = this.createSvgElement('circle', {
      cx: x,
      cy: y,
      r: radius + 12,
      fill: 'none',
      stroke: ringColor,
      'stroke-width': isCenter ? 4 : 3,
      opacity: isCenter ? 0.88 : 0.72,
      class: 'node-region-ring'
    });
    group.appendChild(regionRing);

    group.appendChild(this.createSvgElement('circle', {
      cx: x,
      cy: y,
      r: radius,
      fill: color,
      stroke: ringColor,
      'stroke-width': isCenter ? 2 : 1.5,
      class: 'node-core'
    }));

    const yearLabel = this.createSvgElement('text', {
      x,
      y: y - radius - 12,
      'text-anchor': 'middle',
      fill: isCenter ? '#ffffff' : color,
      'font-size': isCenter ? 13 : 11,
      'font-family': 'JetBrains Mono, monospace',
      'font-weight': 700
    });
    yearLabel.textContent = this.formatYear(event.year);
    group.appendChild(yearLabel);

    const nameLabel = this.createSvgElement('text', {
      x,
      y: y + radius + 18,
      'text-anchor': 'middle',
      fill: this.colors.text,
      'font-size': isCenter ? 14 : 12,
      'font-family': 'Noto Sans SC, sans-serif',
      'font-weight': isCenter ? 700 : 500
    });
    nameLabel.textContent = event.name;
    group.appendChild(nameLabel);

    group.style.opacity = '0';
    group.style.transformOrigin = `${x}px ${y}px`;
    group.style.transform = 'scale(0.82)';
    setTimeout(() => {
      group.style.transition = 'opacity 360ms ease-out, transform 360ms ease-out';
      group.style.opacity = '1';
      group.style.transform = 'scale(1)';
    }, 90);

    if (!isCenter) {
      group.addEventListener('click', () => this.showEvent(event));
    }

    this.svg.appendChild(group);
    this.nodes.push({ element: group, id: event.id, year: event.year, x, y, isCenter, color });
  }

  getRegionRingColor(region) {
    return region === 'china' ? this.colors.chinaRing : this.colors.foreignRing;
  }

  showDetail(event, groups) {
    const relatedGroups = groups || this.getChronologicalGroups(event);
    this.detailPanel.replaceChildren();

    this.detailPanel.appendChild(this.createDetailNode('div', 'event-detail-title', event.name));

    const meta = document.createElement('div');
    meta.className = 'event-detail-meta';
    meta.appendChild(this.createDetailNode('span', 'event-detail-year', this.formatYear(event.year)));
    meta.appendChild(this.createDetailNode('span', 'event-detail-region', event.region === 'china' ? '东方历史' : '西方历史'));
    this.detailPanel.appendChild(meta);

    this.detailPanel.appendChild(this.createDetailNode('div', 'event-detail-desc', event.description));

    this.appendDetailList('更早事件', relatedGroups.earlier.map(item => item.event), 'section-cause');
    this.appendDetailList('更晚事件', relatedGroups.later.map(item => item.event), 'section-effect');

    this.detailPanel.classList.remove('hidden');
  }

  appendDetailList(title, events, sectionClass) {
    if (events.length === 0) return;

    const section = document.createElement('div');
    section.className = `event-detail-section ${sectionClass}`;
    section.appendChild(this.createDetailNode('div', 'event-detail-section-title', title));

    const list = document.createElement('ul');
    list.className = 'event-detail-list';
    events.forEach(event => {
      const item = document.createElement('li');
      item.textContent = event.name;
      item.addEventListener('click', () => this.showEvent(event));
      list.appendChild(item);
    });

    section.appendChild(list);
    this.detailPanel.appendChild(section);
  }

  goBack() {
    if (this.history.length === 0) return;

    const prevId = this.history.pop();
    const prevEvent = DataUtils.getEventById(prevId);
    if (prevEvent) {
      this.centerEvent = prevEvent;
      this.render(prevEvent);
      this.updateBreadcrumb();
    }
  }

  updateBreadcrumb() {
    const breadcrumb = document.getElementById('breadcrumb');
    if (!breadcrumb) return;

    breadcrumb.replaceChildren();
    breadcrumb.appendChild(this.createBreadcrumbItem('历史长河', -1, false));

    this.history.forEach((id, index) => {
      const event = DataUtils.getEventById(id);
      if (event) {
        breadcrumb.appendChild(this.createBreadcrumbSeparator());
        breadcrumb.appendChild(this.createBreadcrumbItem(event.name, index, false));
      }
    });

    if (this.centerEvent) {
      breadcrumb.appendChild(this.createBreadcrumbSeparator());
      breadcrumb.appendChild(this.createBreadcrumbItem(this.centerEvent.name, null, true));
    }
  }

  createBreadcrumbItem(label, index, isCurrent) {
    const item = document.createElement('span');
    item.className = isCurrent ? 'breadcrumb-item current' : 'breadcrumb-item';
    item.textContent = label;

    if (!isCurrent) {
      item.dataset.index = index.toString();
      item.addEventListener('click', () => this.handleBreadcrumbClick(index));
    }

    return item;
  }

  handleBreadcrumbClick(index) {
    if (index === -1) {
      this.history = [];
      if (this.backToChart) {
        this.backToChart();
      }
      return;
    }

    this.history = this.history.slice(0, index + 1);
    const eventId = this.history.pop();
    const event = DataUtils.getEventById(eventId);
    if (event) {
      this.centerEvent = event;
      this.render(event);
      this.updateBreadcrumb();
    }
  }

  createBreadcrumbSeparator() {
    const separator = document.createElement('span');
    separator.className = 'breadcrumb-separator';
    separator.textContent = '›';
    return separator;
  }

  createDetailNode(tagName, className, text) {
    const node = document.createElement(tagName);
    node.className = className;
    node.textContent = text;
    return node;
  }

  createSvgElement(tagName, attributes = {}) {
    const element = document.createElementNS('http://www.w3.org/2000/svg', tagName);
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key, String(value));
    });
    return element;
  }

  formatYear(year) {
    return year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = StarlinkView;
}

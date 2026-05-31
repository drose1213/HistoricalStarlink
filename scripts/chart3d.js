/**
 * 历史星链探索 - 首页地层海报视图
 */

class HistoryChart3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      throw new Error(`HistoryChart3D 初始化失败：未找到容器 ${containerId}`);
    }

    this.events = [];
    this.filter = 'all';
    this.maxEventsPerSide = 5;

    this.colors = {
      earthLayers: [
        '#3b1f12',
        '#6f3b21',
        '#9a674a',
        '#d39c78',
        '#a96b4c',
        '#67371f',
        '#4f2c1c',
        '#70452d',
        '#2f5b66',
        '#72d8e4'
      ]
    };

    this.icons = {
      china: ['▣', '⚔', '☯', '◎', '▤'],
      foreign: ['◑', '✺', '◈', '♜', '⌾']
    };

    this.init();
  }

  init() {
    this.render();
  }

  setFilter(filter) {
    this.filter = this.normalizeFilter(filter);
    this.render();
  }

  render() {
    try {
      this.container.replaceChildren();

      const leftEvents = this.getDisplayEvents('china');
      const rightEvents = this.getDisplayEvents('foreign');
      this.events = [...leftEvents, ...rightEvents];

      const wrapper = document.createElement('div');
      wrapper.className = 'chart-wrapper';

      const coreSection = document.createElement('div');
      coreSection.className = 'core-section';
      coreSection.appendChild(this.createCore());

      wrapper.appendChild(this.createEventList('东方历史', leftEvents, 'left'));
      wrapper.appendChild(coreSection);
      wrapper.appendChild(this.createEventList('西方历史', rightEvents, 'right'));

      this.container.appendChild(wrapper);
      this.addCoreDots();
    } catch (error) {
      this.renderError(error);
    }
  }

  normalizeFilter(filter) {
    return ['all', 'china', 'foreign'].includes(filter) ? filter : 'all';
  }

  renderError(error) {
    const message = document.createElement('div');
    message.className = 'chart-error';
    message.textContent = error instanceof Error ? error.message : '首页历史视图渲染失败';
    this.container.replaceChildren(message);
  }

  getDisplayEvents(region) {
    if (this.filter !== 'all' && this.filter !== region) {
      return [];
    }

    return DataUtils.filterByRegion(region)
      .sort((a, b) => b.year - a.year)
      .slice(0, this.maxEventsPerSide);
  }

  createEventList(title, events, side) {
    const list = document.createElement('div');
    list.className = `event-list ${side}`;

    const label = document.createElement('div');
    label.className = 'list-label';
    label.textContent = title;
    list.appendChild(label);

    const track = document.createElement('div');
    track.className = 'event-track';
    events.forEach((event, index) => {
      track.appendChild(this.createEventItem(event, index, side));
    });
    list.appendChild(track);

    return list;
  }

  createEventItem(event, index, side) {
    const item = document.createElement('div');
    item.className = `event-item ${side}`;
    item.style.setProperty('--event-index', index.toString());

    const iconNode = this.createTextNode('event-icon', this.getIcon(event.region, index));
    const connector = document.createElement('div');
    connector.className = 'event-connector';

    const text = document.createElement('div');
    text.className = 'event-text';
    text.appendChild(this.createTextNode('event-year', this.formatYear(event.year)));
    text.appendChild(this.createTextNode('event-name', event.name));

    if (side === 'left') {
      item.append(iconNode, text, connector);
    } else {
      item.append(connector, text, iconNode);
    }

    item.addEventListener('click', () => {
      if (this.clickHandler) {
        this.clickHandler(event);
      }
    });

    return item;
  }

  createTextNode(className, text) {
    const node = document.createElement('div');
    node.className = className;
    node.textContent = text;
    return node;
  }

  getIcon(region, index) {
    const iconSet = region === 'china' ? this.icons.china : this.icons.foreign;
    return iconSet[index % iconSet.length];
  }

  formatYear(year) {
    return year < 0 ? `约公元前${Math.abs(year)}年` : `${year} CE`;
  }

  createCore() {
    const container = document.createElement('div');
    container.className = 'core-container';

    const core = document.createElement('div');
    core.className = 'core-3d';

    const cylinder = document.createElement('div');
    cylinder.className = 'core-cylinder';

    const layerCount = this.colors.earthLayers.length;
    const layerHeight = 100 / layerCount;
    this.colors.earthLayers.forEach((color, index) => {
      const layer = document.createElement('div');
      layer.className = 'core-layer';
      layer.style.top = `${index * layerHeight}%`;
      layer.style.height = `${layerHeight}%`;
      layer.style.background = color;
      cylinder.appendChild(layer);
    });

    const grass = document.createElement('div');
    grass.className = 'core-top-grass';

    const earth = document.createElement('div');
    earth.className = 'core-earth';

    const timeline = document.createElement('div');
    timeline.className = 'core-timeline';
    ['2000 CE', '1000 CE', '0 CE', '1000 BCE', '3000 BCE'].forEach(label => {
      const mark = document.createElement('span');
      mark.className = 'timeline-mark';
      mark.textContent = label;
      timeline.appendChild(mark);
    });

    core.append(cylinder, grass, earth, timeline);
    container.appendChild(core);

    return container;
  }

  addCoreDots() {
    const cylinder = this.container.querySelector('.core-cylinder');
    if (!cylinder || this.events.length === 0) return;

    const yearRange = DataUtils.getYearRange();
    const rangeSpan = yearRange.max - yearRange.min;
    if (rangeSpan <= 0) return;

    this.events.forEach(event => {
      const dot = document.createElement('div');
      dot.className = `core-dot ${event.region === 'china' ? 'left-side' : 'right-side'}`;
      dot.style.top = `${((yearRange.max - event.year) / rangeSpan) * 80 + 8}%`;
      dot.style.left = event.region === 'china' ? '27%' : '73%';
      dot.setAttribute('title', `${event.name} · ${this.formatYear(event.year)}`);

      dot.addEventListener('click', () => {
        if (this.clickHandler) {
          this.clickHandler(event);
        }
      });

      cylinder.appendChild(dot);
    });
  }

  onEventClick(handler) {
    this.clickHandler = handler;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = HistoryChart3D;
}

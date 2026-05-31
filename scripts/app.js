/**
 * 历史星链探索 - 主入口
 */

(function() {
  'use strict';

  // 状态管理
  const AppState = {
    currentView: 'chart', // 'chart' | 'starlink'
    currentFilter: 'all',
    currentEvent: null,
    exploreHistory: []
  };

  // DOM元素
  const elements = {
    chartView: document.getElementById('chart-view'),
    starlinkView: document.getElementById('starlink-view'),
    filterBtns: document.querySelectorAll('.filter-btn'),
    backBtn: document.getElementById('back-btn')
  };

  // 组件实例
  let chart3d = null;
  let starlink = null;

  // 初始化
  function init() {
    // 初始化3D柱状图
    chart3d = new HistoryChart3D('history-chart3d');
    chart3d.setFilter('all');
    chart3d.onEventClick(handleEventClick);

    // 初始化星链视图
    starlink = new StarlinkView('starlink-svg', 'event-detail');
    starlink.backToChart = goToChart;

    // 绑定事件
    bindEvents();

    // 处理路由
    handleRoute();
  }

  // 绑定事件
  function bindEvents() {
    // 筛选按钮
    elements.filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;
        setFilter(filter);
      });
    });

    // 返回按钮
    elements.backBtn.addEventListener('click', goToChart);

    // 键盘导航
    document.addEventListener('keydown', handleKeyboard);

    // 路由变化
    window.addEventListener('hashchange', handleRoute);
  }

  // 设置筛选
  function setFilter(filter) {
    AppState.currentFilter = filter;

    // 更新按钮状态
    elements.filterBtns.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.filter === filter);
    });

    // 更新3D图表
    chart3d.setFilter(filter);
  }

  // 处理事件点击
  function handleEventClick(event) {
    AppState.currentEvent = event;
    AppState.exploreHistory.push(event.id);

    // 更新URL
    window.location.hash = `/event/${event.id}`;

    // 切换视图
    switchToStarlink(event);
  }

  // 切换到星链视图
  function switchToStarlink(event) {
    AppState.currentView = 'starlink';

    elements.chartView.classList.remove('active');
    elements.starlinkView.classList.add('active');

    starlink.showEvent(event, true);
  }

  // 返回柱状图
  function goToChart() {
    AppState.currentView = 'chart';
    AppState.exploreHistory = [];

    // 更新URL
    window.location.hash = '/';

    elements.starlinkView.classList.remove('active');
    elements.chartView.classList.add('active');
  }

  // 处理路由
  function handleRoute() {
    const hash = window.location.hash || '#/';

    if (hash.startsWith('#/event/')) {
      const eventId = hash.replace('#/event/', '');
      const event = DataUtils.getEventById(eventId);

      if (event) {
        AppState.currentEvent = event;
        switchToStarlink(event);
      } else {
        goToChart();
      }
    } else {
      goToChart();
    }
  }

  // 键盘导航
  function handleKeyboard(e) {
    if (e.key === 'Escape') {
      if (AppState.currentView === 'starlink') {
        goToChart();
      }
    }

    if (e.key === 'Backspace' && AppState.currentView === 'starlink') {
      starlink.goBack();
    }

    // 数字键切换筛选
    if (e.key >= '1' && e.key <= '3') {
      const filters = ['all', 'china', 'foreign'];
      const index = parseInt(e.key) - 1;
      setFilter(filters[index]);
    }
  }

  // 导出到全局（供调试和扩展）
  window.HistoryGame = {
    state: AppState,
    chart3d,
    starlink,
    setFilter,
    goToChart,
    switchToStarlink
  };

  // DOM加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

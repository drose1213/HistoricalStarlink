"""静态验证 HomeView.vue 模板与样式改动"""
from pathlib import Path

p = Path("frontend/src/views/HomeView.vue")
src = p.read_text(encoding="utf-8")
print(f"文件总行数: {len(src.splitlines())}")
print()

print("【1. 关键结构】")
checks = [
    ('<div class="cosmic-overlay" aria-hidden="true">', "cosmic-overlay 空壳"),
    ('<h2 class="drawer-hero-title">探索时空之旅</h2>', "抽屉内 hero 标题"),
    ('<div v-if="drawerOpen" class="event-drawer">', "抽屉容器"),
    ('<div class="drawer-header">', "抽屉 header"),
    ('<div class="search-bar">', "搜索 bar"),
    ('class="drawer-trigger"', "抽屉 trigger"),
]
for marker, desc in checks:
    n = src.count(marker)
    flag = "OK " if n == 1 else "WARN"
    print(f"  [{flag}] {desc}: {n} 处")

print()
print("【2. 清理检查】原 cosmic-overlay 内容应已迁移")
for marker, desc in [
    ('class="hero-copy"', "hero-copy (应 0 处)"),
]:
    n = src.count(marker)
    flag = "OK " if n == 0 else "WARN"
    print(f"  [{flag}] {desc}: {n} 处")

print()
print("【3. CSS 改动检查】")
css_checks = [
    (".event-drawer {", "event-drawer 样式块"),
    ("  top: 90px;", "drawer top: 90px (应 2 处: drawer + trigger)"),
    (".drawer-hero-title {", "hero 标题样式"),
    (".drawer-trigger {", "trigger 样式块"),
    ("display: flex;\n  flex-direction: column;\n  gap: 12px;\n  padding: 18px 18px 16px;", "drawer-header 纵向 flex"),
]
for marker, desc in css_checks:
    n = src.count(marker)
    flag = "OK " if n >= 1 else "WARN"
    print(f"  [{flag}] {desc}: {n} 处")

print()
print("【4. 关键功能事件绑定】")
ev_checks = [
    ("@input=\"onSearchInput\"", "@input 事件"),
    ("@focus=\"showSearchDropdown = true\"", "@focus 事件"),
    ("@blur=\"handleSearchBlur\"", "@blur 事件"),
    ("@keydown.enter=\"handleSearchEnter\"", "@keydown.enter 事件"),
]
for marker, desc in ev_checks:
    n = src.count(marker)
    flag = "OK " if n >= 1 else "WARN"
    print(f"  [{flag}] {desc}: {n} 处")

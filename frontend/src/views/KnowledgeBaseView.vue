<template>
  <div class="kb-view">
    <header class="kb-header">
      <router-link to="/" class="back-link">
        <span>←</span> 返回首页
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">◈</span>
        RAG 知识库管理
      </h2>
      <div class="header-accent"></div>
    </header>

    <main class="kb-main">
      <div class="kb-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="kb-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <div v-if="activeTab === 'overview'" class="tab-content">
        <div class="stats-grid">
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.total }}</span>
            <span class="stat-label">总条目数</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.active }}</span>
            <span class="stat-label">活跃条目</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.by_source?.file_import || 0 }}</span>
            <span class="stat-label">文件导入</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.by_source?.web_crawl || 0 }}</span>
            <span class="stat-label">网页爬取</span>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            数据来源分布
          </h3>
          <div class="source-bars">
            <div v-for="(count, source) in stats.by_source" :key="source" class="source-bar-item">
              <span class="source-label">{{ sourceLabels[source as string] || source }}</span>
              <div class="source-bar-track">
                <div
                  class="source-bar-fill"
                  :style="{ width: stats.total > 0 ? (count / stats.total * 100) + '%' : '0%' }"
                />
              </div>
              <span class="source-count">{{ count }}</span>
            </div>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            区域分布
          </h3>
          <div class="region-grid">
            <div class="region-item">
              <span class="region-dot cn"></span>
              <span class="region-label">中国历史</span>
              <span class="region-count">{{ stats.by_region?.china || 0 }}</span>
            </div>
            <div class="region-item">
              <span class="region-dot foreign"></span>
              <span class="region-label">外国历史</span>
              <span class="region-count">{{ stats.by_region?.foreign || 0 }}</span>
            </div>
          </div>
          <div v-if="stats.latest_update" class="last-update">
            最近更新: {{ stats.latest_update }}
          </div>
        </div>

        <div class="action-row">
          <button class="cy-btn cy-btn--cyan" :disabled="crawling" @click="triggerCrawl">
            {{ crawling ? '爬取中...' : '🔄 立即爬取网页' }}
          </button>
          <button class="cy-btn cy-btn--gold" :disabled="rebuilding" @click="rebuildIndex">
            {{ rebuilding ? '重建中...' : '⚡ 重建 RAG 索引' }}
          </button>
          <button class="cy-btn cy-btn--ghost" :disabled="seeding" @click="triggerSeed">
            {{ seeding ? '导入中...' : '🌱 从种子库导入' }}
          </button>
        </div>
      </div>

      <div v-if="activeTab === 'import'" class="tab-content">
        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            文件导入
          </h3>
          <p class="import-hint">支持 txt / md / csv / json 格式文件，大文件会自动分片存储（每片 2000 字符，重叠 200 字符）</p>

          <div class="file-drop-zone" @dragover.prevent @drop.prevent="handleDrop" @click="triggerFileInput">
            <input ref="fileInputRef" type="file" accept=".txt,.md,.csv,.json,.html" class="file-input-hidden" @change="handleFileSelect" />
            <div v-if="!selectedFile" class="drop-placeholder">
              <span class="drop-icon">📄</span>
              <span>拖拽文件到此处，或点击选择文件</span>
            </div>
            <div v-else class="selected-file">
              <span class="file-icon">📎</span>
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
              <button class="remove-btn" @click.stop="selectedFile = null">✕</button>
            </div>
          </div>

          <div class="import-meta-form">
            <div class="form-row">
              <div class="form-group">
                <label>事件名称</label>
                <input v-model="importMeta.event_name" type="text" placeholder="关联事件名称" class="cy-input" />
              </div>
              <div class="form-group">
                <label>年份</label>
                <input v-model.number="importMeta.year" type="number" placeholder="如: -221, 105" class="cy-input" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>区域</label>
                <select v-model="importMeta.region" class="cy-input">
                  <option value="">不指定</option>
                  <option value="china">中国</option>
                  <option value="foreign">外国</option>
                </select>
              </div>
              <div class="form-group">
                <label>分类</label>
                <select v-model="importMeta.category" class="cy-input">
                  <option value="">不指定</option>
                  <option value="政治">政治</option>
                  <option value="军事">军事</option>
                  <option value="科技">科技</option>
                  <option value="文化">文化</option>
                  <option value="经济">经济</option>
                  <option value="社会">社会</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>标签（逗号分隔）</label>
                <input v-model="importMeta.tags" type="text" placeholder="标签1,标签2,标签3" class="cy-input" />
              </div>
              <div class="form-group">
                <label>重要性 (1-10)</label>
                <input v-model.number="importMeta.importance" type="number" min="1" max="10" placeholder="5" class="cy-input" />
              </div>
            </div>
          </div>

          <button class="cy-btn cy-btn--gold" :disabled="!selectedFile || importing" @click="doImport">
            {{ importing ? '导入中...' : '🚀 开始导入' }}
          </button>

          <div v-if="importResult" class="import-result" :class="importResult.imported > 0 ? 'success' : 'info'">
            <span>{{ importResult.imported > 0 ? '✅' : 'ℹ️' }}</span>
            <span>导入 {{ importResult.imported }} 个分片，跳过 {{ importResult.skipped }} 个重复</span>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            手动添加
          </h3>
          <div class="manual-form">
            <div class="form-group">
              <label>标题 *</label>
              <input v-model="manualForm.title" type="text" placeholder="条目标题" class="cy-input" />
            </div>
            <div class="form-group">
              <label>内容 *</label>
              <textarea v-model="manualForm.content" rows="6" placeholder="条目内容" class="cy-textarea" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>事件名称</label>
                <input v-model="manualForm.event_name" type="text" placeholder="关联事件" class="cy-input" />
              </div>
              <div class="form-group">
                <label>年份</label>
                <input v-model.number="manualForm.year" type="number" placeholder="年份" class="cy-input" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>区域</label>
                <select v-model="manualForm.region" class="cy-input">
                  <option value="">不指定</option>
                  <option value="china">中国</option>
                  <option value="foreign">外国</option>
                </select>
              </div>
              <div class="form-group">
                <label>分类</label>
                <select v-model="manualForm.category" class="cy-input">
                  <option value="">不指定</option>
                  <option value="政治">政治</option>
                  <option value="军事">军事</option>
                  <option value="科技">科技</option>
                  <option value="文化">文化</option>
                  <option value="经济">经济</option>
                  <option value="社会">社会</option>
                </select>
              </div>
            </div>
            <button class="cy-btn cy-btn--cyan" :disabled="!manualForm.title || !manualForm.content || submitting" @click="doManualAdd">
              {{ submitting ? '提交中...' : '➕ 添加条目' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'browse'" class="tab-content">
        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            条件检索
          </h3>
          <p class="import-hint">按需组合筛选条件, 支持区域/分类/年份/重要性/事件名称/标签/来源, 未来页面可直接调用此接口</p>
          <div class="conditional-filters">
            <div class="form-row">
              <div class="form-group">
                <label>关键词</label>
                <input v-model="condFilters.text" type="text" placeholder="标题/事件/内容关键词" class="cy-input" />
              </div>
              <div class="form-group">
                <label>事件名称(模糊)</label>
                <input v-model="condFilters.event_name_like" type="text" placeholder="如: 丝绸" class="cy-input" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>区域</label>
                <select v-model="condFilters.region" class="cy-input">
                  <option value="">不指定</option>
                  <option value="china">中国</option>
                  <option value="foreign">外国</option>
                </select>
              </div>
              <div class="form-group">
                <label>分类</label>
                <select v-model="condFilters.category" class="cy-input">
                  <option value="">不指定</option>
                  <option v-for="c in availableCategories" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>起始年份</label>
                <input v-model.number="condFilters.year_min" type="number" placeholder="如: 0" class="cy-input" />
              </div>
              <div class="form-group">
                <label>结束年份</label>
                <input v-model.number="condFilters.year_max" type="number" placeholder="如: 2000" class="cy-input" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>最低重要性</label>
                <input v-model.number="condFilters.importance_min" type="number" min="1" max="10" placeholder="1-10" class="cy-input" />
              </div>
              <div class="form-group">
                <label>标签(可选)</label>
                <input v-model="condFilters.tag" type="text" placeholder="如: 战争" class="cy-input" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>排序方式</label>
                <select v-model="condFilters.order_by" class="cy-input">
                  <option value="relevance">按相关性/重要性</option>
                  <option value="importance">按重要性</option>
                  <option value="year">按年份</option>
                  <option value="updated_at">按更新时间</option>
                </select>
              </div>
              <div class="form-group">
                <label>每页条数</label>
                <input v-model.number="condFilters.page_size" type="number" min="1" max="100" placeholder="20" class="cy-input" />
              </div>
            </div>
            <div class="action-row">
              <button class="cy-btn cy-btn--cyan" @click="doConditionalSearch">🔍 条件检索</button>
              <button class="cy-btn cy-btn--ghost" @click="resetConditional">重置</button>
            </div>
            <div v-if="conditionalResult" class="import-result info">
              <span>ℹ️</span>
              <span>匹配 {{ conditionalResult.total }} 条 · 显示 {{ conditionalResult.items?.length || 0 }} 条 · 第 {{ conditionalResult.page || 1 }} / {{ Math.max(1, Math.ceil(conditionalResult.total / (conditionalResult.page_size || 20))) }} 页</span>
            </div>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            知识库条目
          </h3>

          <div class="filter-bar">
            <input v-model="filters.keyword" type="text" placeholder="搜索标题/事件/内容" class="cy-input filter-input" @input="debounceFetch" />
            <select v-model="filters.source_type" class="cy-input filter-select" @change="fetchEntries">
              <option value="">全部来源</option>
              <option value="file_import">文件导入</option>
              <option value="web_crawl">网页爬取</option>
              <option value="manual">手动添加</option>
              <option value="seed_data">种子数据</option>
            </select>
            <select v-model="filters.region" class="cy-input filter-select" @change="fetchEntries">
              <option value="">全部区域</option>
              <option value="china">中国</option>
              <option value="foreign">外国</option>
            </select>
            <select v-model="filters.status" class="cy-input filter-select" @change="fetchEntries">
              <option value="">全部状态</option>
              <option value="active">活跃</option>
              <option value="archived">已归档</option>
              <option value="pending_review">待审核</option>
            </select>
          </div>

          <div v-if="entriesLoading" class="loading-state">
            <div class="cy-loading"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="entries.length === 0" class="empty-state">
            <div class="empty-icon">◇</div>
            <p>暂无条目</p>
          </div>

          <div v-else class="entries-list">
            <div v-for="entry in entries" :key="entry.id" class="entry-card" @click="viewEntry(entry)">
              <div class="entry-head">
                <span class="entry-source-badge" :class="entry.source_type">
                  {{ sourceLabels[entry.source_type] || entry.source_type }}
                </span>
                <span class="entry-version">v{{ entry.version }}</span>
                <span v-if="entry.version_count && entry.version_count > 1" class="entry-version-total">
                  ({{ entry.version_count }} 个历史版本)
                </span>
                <span class="entry-status-badge" :class="entry.status">
                  {{ statusLabels[entry.status] || entry.status }}
                </span>
              </div>
              <h4 class="entry-title">{{ entry.title }}</h4>
              <p class="entry-preview">{{ entry.content_preview }}</p>
              <div class="entry-meta">
                <span v-if="entry.event_name" class="meta-item">📌 {{ entry.event_name }}</span>
                <span v-if="entry.year" class="meta-item">📅 {{ entry.year < 0 ? '前' + Math.abs(entry.year) : entry.year }}年</span>
                <span v-if="entry.region" class="meta-item">{{ entry.region === 'china' ? '🇨🇳' : '🌍' }} {{ entry.region === 'china' ? '中国' : '外国' }}</span>
                <span v-if="entry.category" class="meta-item">📁 {{ entry.category }}</span>
                <span v-if="entry.tags && entry.tags.length" class="meta-item">🏷 {{ entry.tags.slice(0, 3).join(', ') }}</span>
                <span v-if="entry.importance" class="meta-item">⭐ {{ entry.importance }}/10</span>
              </div>
              <div class="entry-footer">
                <span class="chunk-info">分片 {{ entry.chunk_index + 1 }}/{{ entry.chunk_total }}</span>
                <span class="entry-date">{{ entry.created_at?.split('T')[0] || entry.created_at?.split(' ')[0] || '' }}</span>
                <button class="delete-btn" @click.stop="deleteEntry(entry.id)" title="删除">🗑</button>
              </div>
            </div>
          </div>

          <div v-if="entriesTotal > pageSize" class="pagination">
            <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage--; fetchEntries()">上一页</button>
            <span class="page-info">{{ currentPage }} / {{ Math.ceil(entriesTotal / pageSize) }}</span>
            <button class="page-btn" :disabled="currentPage >= Math.ceil(entriesTotal / pageSize)" @click="currentPage++; fetchEntries()">下一页</button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'sources'" class="tab-content">
        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            推荐爬虫来源
          </h3>
          <p class="import-hint">系统每日自动遍历以下推荐来源, 按 event_name 去重后写入知识库</p>
          <div v-if="crawlSources.length === 0" class="empty-state">
            <p>暂无推荐来源</p>
          </div>
          <div v-else class="crawl-sources-list">
            <div v-for="src in crawlSources" :key="src.id" class="crawl-source-card">
              <div class="crawl-source-head">
                <span class="crawl-source-name">{{ src.name }}</span>
                <span class="entry-status-badge" :class="src.last_status === 'success' ? 'active' : src.last_status === 'failed' ? 'archived' : 'pending_review'">
                  {{ src.last_status === 'success' ? '✅ 成功' : src.last_status === 'failed' ? '❌ 失败' : '⏳ 待爬' }}
                </span>
                <span v-if="src.recommended" class="entry-source-badge seed_data">推荐</span>
              </div>
              <a class="crawl-source-url" :href="src.url" target="_blank" rel="noopener">{{ src.url }}</a>
              <p v-if="src.description" class="crawl-source-desc">{{ src.description }}</p>
              <div class="crawl-source-meta">
                <span v-if="src.category">📁 {{ src.category }}</span>
                <span v-if="src.region">🌍 {{ src.region === 'china' ? '中国' : src.region === 'foreign' ? '外国' : src.region }}</span>
                <span v-if="src.last_imported !== null">📥 上次导入 {{ src.last_imported }} 条</span>
                <span v-if="src.last_crawled_at">🕐 {{ src.last_crawled_at }}</span>
              </div>
              <div v-if="src.tags && src.tags.length" class="tag-list">
                <span v-for="tag in src.tags" :key="tag" class="tag-chip">{{ tag }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'detail' && selectedEntry" class="tab-content">
        <div class="section-block cy-card">
          <div class="detail-header">
            <button class="cy-btn cy-btn--ghost" @click="activeTab = 'browse'">← 返回列表</button>
            <div class="detail-actions">
              <button class="cy-btn cy-btn--ghost" :disabled="versionsLoading" @click="fetchVersions(selectedEntry.id)">
                {{ versionsLoading ? '加载中...' : '📚 版本历史' }}
              </button>
              <button class="cy-btn cy-btn--ghost" @click="deleteEntry(selectedEntry.id)">🗑 删除</button>
            </div>
          </div>

          <div v-if="showVersions && entryVersions.length" class="version-history">
            <h4 class="version-history-title">版本历史 (共 {{ entryVersions.length }} 个版本)</h4>
            <div class="version-list">
              <div v-for="v in entryVersions" :key="v.id" class="version-item">
                <div class="version-item-head">
                  <span class="version-num">v{{ v.version }}</span>
                  <span class="version-source-badge">{{ v.change_source || 'system' }}</span>
                  <span class="version-date">{{ v.created_at }}</span>
                </div>
                <div class="version-summary">{{ v.change_summary || '无变更说明' }}</div>
                <div class="version-meta">
                  <span v-if="v.operator">操作者: {{ v.operator }}</span>
                  <span class="mono">hash: {{ v.content_hash?.substring(0, 12) }}...</span>
                </div>
                <div v-if="v.snapshot_meta" class="version-snapshot">
                  <details>
                    <summary>查看元数据快照</summary>
                    <pre class="snapshot-pre">{{ JSON.stringify(v.snapshot_meta, null, 2) }}</pre>
                  </details>
                </div>
              </div>
            </div>
          </div>

          <h3 class="detail-title">{{ selectedEntry.title }}</h3>

          <div class="detail-meta-grid">
            <div class="meta-field">
              <span class="meta-label">来源</span>
              <span class="meta-value">{{ sourceLabels[selectedEntry.source_type] || selectedEntry.source_type }}</span>
            </div>
            <div class="meta-field">
              <span class="meta-label">版本</span>
              <span class="meta-value">v{{ selectedEntry.version }}</span>
            </div>
            <div class="meta-field">
              <span class="meta-label">状态</span>
              <span class="meta-value">{{ statusLabels[selectedEntry.status] || selectedEntry.status }}</span>
            </div>
            <div class="meta-field">
              <span class="meta-label">分片</span>
              <span class="meta-value">{{ selectedEntry.chunk_index + 1 }} / {{ selectedEntry.chunk_total }}</span>
            </div>
            <div v-if="selectedEntry.event_name" class="meta-field">
              <span class="meta-label">事件</span>
              <span class="meta-value">{{ selectedEntry.event_name }}</span>
            </div>
            <div v-if="selectedEntry.year" class="meta-field">
              <span class="meta-label">年份</span>
              <span class="meta-value">{{ selectedEntry.year < 0 ? '公元前' + Math.abs(selectedEntry.year) : '公元' + selectedEntry.year + '年' }}</span>
            </div>
            <div v-if="selectedEntry.region" class="meta-field">
              <span class="meta-label">区域</span>
              <span class="meta-value">{{ selectedEntry.region === 'china' ? '中国' : '外国' }}</span>
            </div>
            <div v-if="selectedEntry.category" class="meta-field">
              <span class="meta-label">分类</span>
              <span class="meta-value">{{ selectedEntry.category }}</span>
            </div>
            <div v-if="selectedEntry.importance" class="meta-field">
              <span class="meta-label">重要性</span>
              <span class="meta-value">{{ selectedEntry.importance }}/10</span>
            </div>
            <div v-if="selectedEntry.source_url" class="meta-field meta-field--wide">
              <span class="meta-label">来源URL</span>
              <a class="meta-value link" :href="selectedEntry.source_url" target="_blank">{{ selectedEntry.source_url }}</a>
            </div>
            <div v-if="selectedEntry.file_name" class="meta-field">
              <span class="meta-label">文件名</span>
              <span class="meta-value">{{ selectedEntry.file_name }}</span>
            </div>
            <div v-if="selectedEntry.content_hash" class="meta-field meta-field--wide">
              <span class="meta-label">内容哈希</span>
              <span class="meta-value mono">{{ selectedEntry.content_hash?.substring(0, 16) }}...</span>
            </div>
            <div v-if="selectedEntry.tags && selectedEntry.tags.length" class="meta-field meta-field--wide">
              <span class="meta-label">标签</span>
              <div class="tag-list">
                <span v-for="tag in selectedEntry.tags" :key="tag" class="tag-chip">{{ tag }}</span>
              </div>
            </div>
            <div v-if="selectedEntry.figures && selectedEntry.figures.length" class="meta-field meta-field--wide">
              <span class="meta-label">人物</span>
              <div class="tag-list">
                <span v-for="fig in selectedEntry.figures" :key="fig" class="tag-chip figure">{{ fig }}</span>
              </div>
            </div>
          </div>

          <div class="detail-content">
            <h4 class="content-label">正文内容</h4>
            <div class="content-body">{{ selectedEntry.content }}</div>
          </div>

          <div class="detail-dates">
            <span>创建: {{ selectedEntry.created_at }}</span>
            <span>更新: {{ selectedEntry.updated_at }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ragApi, type KnowledgeEntry, type KnowledgeStats, type KnowledgeVersion, type CrawlSource } from '@/api/rag'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: '概览', icon: '◈' },
  { key: 'import', label: '导入', icon: '📄' },
  { key: 'browse', label: '浏览', icon: '🔍' },
  { key: 'sources', label: '爬虫源', icon: '🌐' },
]

const stats = reactive<KnowledgeStats>({
  total: 0, active: 0,
  by_source: {},
  by_region: {},
  latest_update: null,
})

const sourceLabels: Record<string, string> = {
  file_import: '文件导入',
  web_crawl: '网页爬取',
  manual: '手动添加',
  seed_data: '种子数据',
}

const availableCategories = computed(() => {
  const cats = new Set<string>()
  entries.value.forEach(e => { if (e.category) cats.add(e.category) })
  conditionalResult.value?.items?.forEach((e: any) => { if (e.category) cats.add(e.category) })
  return Array.from(cats).sort()
})

const statusLabels: Record<string, string> = {
  active: '活跃',
  archived: '已归档',
  pending_review: '待审核',
}

const crawling = ref(false)
const rebuilding = ref(false)
const seeding = ref(false)
const crawlSources = ref<CrawlSource[]>([])

const condFilters = reactive({
  text: '',
  event_name_like: '',
  region: '',
  category: '',
  year_min: undefined as number | undefined,
  year_max: undefined as number | undefined,
  importance_min: undefined as number | undefined,
  tag: '',
  order_by: 'relevance' as 'relevance' | 'importance' | 'year' | 'updated_at',
  page_size: 20,
})
const conditionalResult = ref<any>(null)

const entryVersions = ref<KnowledgeVersion[]>([])
const versionsLoading = ref(false)
const showVersions = ref(false)

const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const importing = ref(false)
const importResult = ref<{ imported: number; skipped: number } | null>(null)
const importMeta = reactive({
  event_name: '', year: undefined as number | undefined,
  region: '', category: '', tags: '', importance: undefined as number | undefined,
})

const manualForm = reactive({
  title: '', content: '', event_name: '', year: undefined as number | undefined,
  region: '', category: '',
})
const submitting = ref(false)

const entries = ref<KnowledgeEntry[]>([])
const entriesTotal = ref(0)
const entriesLoading = ref(false)
const currentPage = ref(1)
const pageSize = 20
const filters = reactive({ keyword: '', source_type: '', region: '', status: '' })

const selectedEntry = ref<KnowledgeEntry | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null
function debounceFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { currentPage.value = 1; fetchEntries() }, 400)
}

async function fetchStats() {
  try {
    const res = await ragApi.getStats()
    if (res.code === 200 && res.data) {
      Object.assign(stats, res.data)
    }
  } catch { /* ignore */ }
}

async function triggerCrawl() {
  crawling.value = true
  try {
    const res = await ragApi.triggerCrawl()
    if (res.code === 200) {
      appStore.showToast('success', `爬取完成，导入 ${res.data?.imported || 0} 个条目`)
      fetchStats()
      fetchCrawlSources()
    }
  } catch {
    appStore.showToast('error', '爬取失败')
  } finally {
    crawling.value = false
  }
}

async function triggerSeed() {
  seeding.value = true
  try {
    const res = await ragApi.importSeed()
    if (res.code === 200) {
      appStore.showToast(
        'success',
        `种子导入完成: 新增 ${res.data?.imported || 0} 条, 跳过 ${res.data?.skipped || 0} 条, 共 ${res.data?.total_events || 0} 个事件`,
      )
      fetchStats()
    }
  } catch {
    appStore.showToast('error', '种子导入失败')
  } finally {
    seeding.value = false
  }
}

async function fetchCrawlSources() {
  try {
    const res = await ragApi.listCrawlSources({ recommended: 1 })
    if (res.code === 200) {
      crawlSources.value = res.data?.items || []
    }
  } catch { /* ignore */ }
}

async function doConditionalSearch() {
  try {
    const res = await ragApi.conditionalSearch({
      text: condFilters.text || undefined,
      event_name_like: condFilters.event_name_like || undefined,
      region: condFilters.region || undefined,
      category: condFilters.category || undefined,
      year_min: condFilters.year_min,
      year_max: condFilters.year_max,
      importance_min: condFilters.importance_min,
      tag: condFilters.tag || undefined,
      order_by: condFilters.order_by,
      page_size: condFilters.page_size,
      page: 1,
    })
    if (res.code === 200 && res.data) {
      conditionalResult.value = res.data
      appStore.showToast('success', `匹配 ${res.data.total} 条结果`)
    }
  } catch {
    appStore.showToast('error', '条件检索失败')
  }
}

function resetConditional() {
  condFilters.text = ''
  condFilters.event_name_like = ''
  condFilters.region = ''
  condFilters.category = ''
  condFilters.year_min = undefined
  condFilters.year_max = undefined
  condFilters.importance_min = undefined
  condFilters.tag = ''
  condFilters.order_by = 'relevance'
  condFilters.page_size = 20
  conditionalResult.value = null
}

async function fetchVersions(entryId: number) {
  versionsLoading.value = true
  try {
    const res = await ragApi.getEntryVersions(entryId)
    if (res.code === 200) {
      entryVersions.value = res.data?.items || []
      showVersions.value = true
    }
  } catch { /* ignore */ } finally {
    versionsLoading.value = false
  }
}

async function rebuildIndex() {
  rebuilding.value = true
  try {
    const res = await ragApi.rebuild()
    if (res.code === 200) {
      appStore.showToast('success', `索引重建完成: ${res.data?.mode} 模式，${res.data?.count} 条`)
    }
  } catch {
    appStore.showToast('error', '索引重建失败')
  } finally {
    rebuilding.value = false
  }
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) selectedFile.value = input.files[0]
}

function handleDrop(e: DragEvent) {
  if (e.dataTransfer?.files?.[0]) selectedFile.value = e.dataTransfer.files[0]
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

async function doImport() {
  if (!selectedFile.value) return
  importing.value = true
  importResult.value = null
  try {
    const meta: any = {}
    if (importMeta.event_name) meta.event_name = importMeta.event_name
    if (importMeta.year) meta.year = importMeta.year
    if (importMeta.region) meta.region = importMeta.region
    if (importMeta.category) meta.category = importMeta.category
    if (importMeta.tags) meta.tags = importMeta.tags
    if (importMeta.importance) meta.importance = importMeta.importance
    const res = await ragApi.importFile(selectedFile.value, meta)
    if (res.code === 200) {
      importResult.value = res.data
      appStore.showToast('success', `导入成功: ${res.data?.imported || 0} 个分片`)
      fetchStats()
      selectedFile.value = null
    }
  } catch {
    appStore.showToast('error', '导入失败')
  } finally {
    importing.value = false
  }
}

async function doManualAdd() {
  if (!manualForm.title || !manualForm.content) return
  submitting.value = true
  try {
    const res = await ragApi.addManualEntry({
      title: manualForm.title,
      content: manualForm.content,
      event_name: manualForm.event_name || undefined,
      year: manualForm.year,
      region: manualForm.region || undefined,
      category: manualForm.category || undefined,
    })
    if (res.code === 200) {
      appStore.showToast('success', `添加成功: ${res.data?.imported || 0} 个分片`)
      manualForm.title = ''
      manualForm.content = ''
      manualForm.event_name = ''
      fetchStats()
    }
  } catch {
    appStore.showToast('error', '添加失败')
  } finally {
    submitting.value = false
  }
}

async function fetchEntries() {
  entriesLoading.value = true
  try {
    const res = await ragApi.getEntries({
      source_type: filters.source_type || undefined,
      region: filters.region || undefined,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined,
      page: currentPage.value,
      page_size: pageSize,
    })
    if (res.code === 200 && res.data) {
      entries.value = res.data.items
      entriesTotal.value = res.data.total
    }
  } catch { /* ignore */ } finally {
    entriesLoading.value = false
  }
}

async function viewEntry(entry: KnowledgeEntry) {
  try {
    const res = await ragApi.getEntry(entry.id)
    if (res.code === 200 && res.data) {
      selectedEntry.value = res.data
      showVersions.value = false
      entryVersions.value = []
      activeTab.value = 'detail'
    }
  } catch { /* ignore */ }
}

async function deleteEntry(id: number) {
  if (!confirm('确定删除此条目？')) return
  try {
    await ragApi.deleteEntry(id)
    appStore.showToast('success', '删除成功')
    fetchEntries()
    fetchStats()
    if (selectedEntry.value?.id === id) {
      selectedEntry.value = null
      activeTab.value = 'browse'
    }
  } catch {
    appStore.showToast('error', '删除失败')
  }
}

watch(activeTab, (tab) => {
  if (tab === 'overview') fetchStats()
  if (tab === 'browse') fetchEntries()
  if (tab === 'sources') fetchCrawlSources()
})

onMounted(() => { fetchStats(); fetchCrawlSources() })
</script>

<style scoped>
.kb-view {
  min-height: 100vh;
  background: var(--bg-primary);
}

.kb-header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 14px 28px;
  display: flex;
  align-items: center;
  gap: 24px;
  background: linear-gradient(180deg, rgba(4, 8, 15, 0.98) 0%, rgba(4, 8, 15, 0.88) 100%);
  border-bottom: 1px solid var(--border-subtle);
  backdrop-filter: blur(12px);
}

.back-link {
  font-size: 13px;
  color: var(--cyan-core);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
  white-space: nowrap;
  flex-shrink: 0;
}

.back-link:hover {
  background: rgba(49, 247, 255, 0.1);
}

.page-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 800;
  color: var(--accent-gold);
  text-shadow: 0 0 20px rgba(212, 168, 75, 0.5);
  letter-spacing: 3px;
  flex: 1;
  text-align: center;
}

.title-icon { margin-right: 8px; }

.header-accent { width: 40px; flex-shrink: 0; }

.kb-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 28px;
  background: rgba(8, 15, 28, 0.6);
  border-bottom: 1px solid var(--border-subtle);
}

.kb-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.25s;
  color: var(--text-muted);
  font-size: 14px;
}

.kb-tab:hover { background: rgba(255, 255, 255, 0.04); color: var(--text-light); }

.kb-tab.active {
  background: rgba(49, 247, 255, 0.12);
  border-color: var(--border-cyan);
  color: #fff;
}

.kb-main { padding: 28px; max-width: 1000px; margin: 0 auto; }

.tab-content { animation: fadeIn 0.3s ease; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-value {
  display: block;
  font-family: var(--font-mono);
  font-size: 32px;
  font-weight: 800;
  color: var(--cyan-core);
  text-shadow: 0 0 16px rgba(49, 247, 255, 0.3);
}

.stat-label {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.section-block { margin-bottom: 20px; padding: 24px; }

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-light);
  margin-bottom: 16px;
}

.section-icon { color: var(--cyan-core); font-size: 14px; }

.source-bars { display: flex; flex-direction: column; gap: 10px; }

.source-bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.source-label { width: 80px; font-size: 13px; color: var(--text-muted); text-align: right; }

.source-bar-track {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.source-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cyan-core), var(--pink-core));
  border-radius: 4px;
  transition: width 0.5s ease;
}

.source-count { width: 40px; font-family: var(--font-mono); font-size: 13px; color: var(--text-light); }

.region-grid { display: flex; gap: 24px; }

.region-item { display: flex; align-items: center; gap: 8px; }

.region-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.region-dot.cn { background: var(--cyan-core); box-shadow: 0 0 8px var(--cyan-core); }
.region-dot.foreign { background: var(--pink-core); box-shadow: 0 0 8px var(--pink-core); }

.region-label { font-size: 13px; color: var(--text-muted); }
.region-count { font-family: var(--font-mono); font-size: 15px; color: var(--text-light); font-weight: 700; }

.last-update {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.import-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
  line-height: 1.6;
}

.file-drop-zone {
  border: 2px dashed rgba(49, 247, 255, 0.3);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s;
  margin-bottom: 20px;
}

.file-drop-zone:hover { border-color: var(--cyan-core); background: rgba(49, 247, 255, 0.04); }

.file-input-hidden { display: none; }

.drop-placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-muted); }
.drop-icon { font-size: 32px; }

.selected-file {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.file-icon { font-size: 20px; }
.file-name { color: var(--text-light); font-weight: 600; }
.file-size { color: var(--text-muted); font-family: var(--font-mono); font-size: 12px; }

.remove-btn {
  background: rgba(255, 100, 100, 0.15);
  border: 1px solid rgba(255, 100, 100, 0.3);
  color: #ff6464;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.import-meta-form { margin-bottom: 20px; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }

.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 12px; color: var(--text-muted); letter-spacing: 0.5px; }

.cy-input {
  background: rgba(2, 5, 11, 0.7);
  border: 1px solid var(--border-subtle);
  color: var(--text-light);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.cy-input:focus { border-color: var(--cyan-core); }

.cy-textarea {
  background: rgba(2, 5, 11, 0.7);
  border: 1px solid var(--border-subtle);
  color: var(--text-light);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  resize: vertical;
  font-family: inherit;
  transition: border-color 0.2s;
}

.cy-textarea:focus { border-color: var(--cyan-core); }

.import-result {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.import-result.success { background: rgba(49, 247, 255, 0.08); border: 1px solid rgba(49, 247, 255, 0.2); color: var(--cyan-core); }
.import-result.info { background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border-subtle); color: var(--text-muted); }

.manual-form { display: flex; flex-direction: column; gap: 12px; }

.cy-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.cy-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.cy-btn--cyan {
  background: rgba(49, 247, 255, 0.12);
  border-color: var(--border-cyan);
  color: var(--cyan-core);
}

.cy-btn--cyan:hover:not(:disabled) { background: rgba(49, 247, 255, 0.2); }

.cy-btn--gold {
  background: rgba(212, 168, 75, 0.12);
  border-color: rgba(212, 168, 75, 0.4);
  color: var(--accent-gold);
}

.cy-btn--gold:hover:not(:disabled) { background: rgba(212, 168, 75, 0.2); }

.cy-btn--ghost {
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
}

.cy-btn--ghost:hover { border-color: var(--border-cyan); color: var(--text-light); }

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-input { flex: 1; min-width: 200px; }
.filter-select { width: 130px; }

.entries-list { display: flex; flex-direction: column; gap: 8px; }

.entry-card {
  padding: 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s;
}

.entry-card:hover { border-color: var(--border-cyan); background: rgba(49, 247, 255, 0.03); }

.entry-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }

.entry-source-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
}

.entry-source-badge.file_import { background: rgba(49, 247, 255, 0.12); color: var(--cyan-core); border: 1px solid rgba(49, 247, 255, 0.3); }
.entry-source-badge.web_crawl { background: rgba(255, 53, 243, 0.12); color: var(--pink-core); border: 1px solid rgba(255, 53, 243, 0.3); }
.entry-source-badge.manual { background: rgba(212, 168, 75, 0.12); color: var(--accent-gold); border: 1px solid rgba(212, 168, 75, 0.3); }
.entry-source-badge.seed_data { background: rgba(128, 128, 128, 0.12); color: var(--text-muted); border: 1px solid rgba(128, 128, 128, 0.3); }

.entry-version { font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); }

.entry-status-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
}

.entry-status-badge.active { color: #4caf50; }
.entry-status-badge.archived { color: var(--text-muted); }
.entry-status-badge.pending_review { color: #ff9800; }

.entry-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-light);
  margin-bottom: 6px;
}

.entry-preview {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.entry-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.meta-item { font-size: 11px; color: var(--text-muted); }

.entry-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: var(--text-muted);
}

.chunk-info { font-family: var(--font-mono); }
.entry-date { margin-left: auto; }

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.4;
  transition: opacity 0.2s;
  font-size: 14px;
}

.delete-btn:hover { opacity: 1; }

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.page-btn {
  padding: 6px 14px;
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid var(--border-subtle);
  color: var(--text-light);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-btn:hover:not(:disabled) { border-color: var(--border-cyan); }

.page-info { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.detail-actions { display: flex; gap: 8px; }

.detail-title {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-light);
  margin-bottom: 20px;
}

.detail-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.meta-field { display: flex; flex-direction: column; gap: 2px; }
.meta-field--wide { grid-column: 1 / -1; }

.meta-label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.5px; text-transform: uppercase; }
.meta-value { font-size: 13px; color: var(--text-light); }
.meta-value.link { color: var(--cyan-core); text-decoration: underline; word-break: break-all; }
.meta-value.mono { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }

.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }

.tag-chip {
  padding: 2px 10px;
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid rgba(49, 247, 255, 0.2);
  border-radius: var(--radius-full);
  font-size: 11px;
  color: var(--cyan-core);
}

.tag-chip.figure {
  background: rgba(212, 168, 75, 0.08);
  border-color: rgba(212, 168, 75, 0.2);
  color: var(--accent-gold);
}

.detail-content { margin-top: 20px; }

.content-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.content-body {
  background: rgba(2, 5, 11, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-light);
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

.detail-dates {
  margin-top: 16px;
  display: flex;
  gap: 24px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  gap: 8px;
  color: var(--text-muted);
}

.cy-loading {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(49, 247, 255, 0.15);
  border-top-color: var(--cyan-core);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-icon { font-size: 32px; opacity: 0.3; }

/* 新增: 条件检索 */
.conditional-filters { display: flex; flex-direction: column; gap: 8px; }

/* 新增: 爬虫源 */
.crawl-sources-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px; }
.crawl-source-card {
  padding: 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: rgba(2, 6, 13, 0.4);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.crawl-source-head { display: flex; align-items: center; gap: 8px; }
.crawl-source-name { font-size: 14px; font-weight: 700; color: var(--text-light); }
.crawl-source-url {
  font-size: 11px;
  color: var(--cyan-core);
  text-decoration: none;
  word-break: break-all;
  font-family: var(--font-mono);
}
.crawl-source-url:hover { text-decoration: underline; }
.crawl-source-desc { font-size: 12px; color: var(--text-muted); line-height: 1.5; margin: 0; }
.crawl-source-meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: 11px; color: var(--text-muted); }

/* 新增: 版本历史 */
.version-history { margin-bottom: 20px; padding: 16px; background: rgba(2, 5, 11, 0.4); border: 1px solid var(--border-subtle); border-radius: 10px; }
.version-history-title { font-size: 14px; color: var(--text-light); margin: 0 0 12px; }
.version-list { display: flex; flex-direction: column; gap: 8px; }
.version-item {
  padding: 10px 12px;
  background: rgba(8, 15, 28, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
}
.version-item-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.version-num { font-family: var(--font-mono); font-size: 12px; color: var(--cyan-core); font-weight: 700; }
.version-source-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 3px;
  background: rgba(49, 247, 255, 0.1); color: var(--cyan-core);
  border: 1px solid rgba(49, 247, 255, 0.3);
}
.version-date { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); margin-left: auto; }
.version-summary { font-size: 12px; color: var(--text-light); line-height: 1.5; }
.version-meta { display: flex; gap: 12px; font-size: 10px; color: var(--text-muted); margin-top: 4px; }
.version-snapshot { margin-top: 6px; font-size: 11px; color: var(--text-muted); }
.version-snapshot details summary { cursor: pointer; color: var(--cyan-core); }
.snapshot-pre {
  background: rgba(0, 0, 0, 0.4);
  padding: 8px;
  border-radius: 4px;
  font-size: 10px;
  font-family: var(--font-mono);
  overflow-x: auto;
  margin-top: 4px;
}

.entry-version-total { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); }

@media (max-width: 640px) {
  .kb-header { padding: 12px 16px; gap: 12px; }
  .page-title { font-size: 16px; letter-spacing: 2px; }
  .kb-tabs { padding: 10px 16px; overflow-x: auto; }
  .kb-tab { padding: 8px 14px; font-size: 13px; white-space: nowrap; }
  .kb-main { padding: 16px; }
  .form-row { grid-template-columns: 1fr; }
  .filter-bar { flex-direction: column; }
  .filter-select { width: 100%; }
  .detail-meta-grid { grid-template-columns: 1fr; }
}
</style>

<template>
  <div class="kb-view">
    <header class="kb-header">
      <router-link to="/" class="back-link">
        <span><</span> Home
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">*</span>
        RAG Knowledge Base
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
            <span class="stat-label">Total Entries</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.active }}</span>
            <span class="stat-label">Active Entries</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.by_source?.file_import || 0 }}</span>
            <span class="stat-label">File Imports</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.by_source?.web_crawl || 0 }}</span>
            <span class="stat-label">Web Crawls</span>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">*</span>
            Source Distribution
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
            <span class="section-icon">*</span>
            Region Distribution
          </h3>
          <div class="region-grid">
            <div class="region-item">
              <span class="region-dot cn"></span>
              <span class="region-label">China</span>
              <span class="region-count">{{ stats.by_region?.china || 0 }}</span>
            </div>
            <div class="region-item">
              <span class="region-dot foreign"></span>
              <span class="region-label">Foreign</span>
              <span class="region-count">{{ stats.by_region?.foreign || 0 }}</span>
            </div>
          </div>
          <div v-if="stats.latest_update" class="last-update">
            Latest update: {{ stats.latest_update }}
          </div>
        </div>

        <div class="action-row">
          <button class="cy-btn cy-btn--cyan" :disabled="crawling" @click="triggerCrawl">
            {{ crawling ? 'Crawling...' : 'Run Crawl Now' }}
          </button>
          <button class="cy-btn cy-btn--gold" :disabled="rebuilding" @click="rebuildIndex">
            {{ rebuilding ? 'Rebuilding...' : 'Rebuild RAG Index' }}
          </button>
          <button class="cy-btn cy-btn--ghost" :disabled="seeding" @click="triggerSeed">
            {{ seeding ? 'Importing...' : 'Import Seeds' }}
          </button>
        </div>
      </div>

      <div v-if="activeTab === 'import'" class="tab-content">
        <div class="import-layout">
          <div class="section-block cy-card import-primary-card">
            <div class="panel-header-row">
              <div>
                <h3 class="section-title">
                  <span class="section-icon">+</span>
                  File Import
                </h3>
                <p class="import-hint">Upload txt, md, csv, json, or html files. Large files are chunked automatically for later retrieval.</p>
              </div>
              <div class="import-chip-row">
                <span class="import-chip">Drag & Drop</span>
                <span class="import-chip">Auto Chunk</span>
                <span class="import-chip">Metadata Ready</span>
              </div>
            </div>

            <div class="file-drop-zone" @dragover.prevent @drop.prevent="handleDrop" @click="triggerFileInput">
              <input ref="fileInputRef" type="file" accept=".txt,.md,.csv,.json,.html" class="file-input-hidden" @change="handleFileSelect" />
              <div v-if="!selectedFile" class="drop-placeholder">
                <span class="drop-icon">v</span>
                <span>Drop a file here or click to choose one</span>
              </div>
              <div v-else class="selected-file selected-file--wide">
                <span class="file-icon">[]</span>
                <div class="selected-file-meta">
                  <span class="file-name">{{ selectedFile.name }}</span>
                  <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                </div>
                <button class="remove-btn" @click.stop="selectedFile = null">x</button>
              </div>
            </div>

            <div class="import-meta-form">
              <div class="form-row">
                <div class="form-group">
                  <label>Event Name</label>
                  <input v-model="importMeta.event_name" type="text" placeholder="Linked event name" class="cy-input" />
                </div>
                <div class="form-group">
                  <label>Year</label>
                  <input v-model.number="importMeta.year" type="number" placeholder="e.g. -221 / 1911" class="cy-input" />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Region</label>
                  <select v-model="importMeta.region" class="cy-input">
                    <option value="">Any</option>
                    <option value="china">China</option>
                    <option value="foreign">Foreign</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Category</label>
                  <select v-model="importMeta.category" class="cy-input">
                    <option value="">Any</option>
                    <option value="&#25919;&#27835;">Politics</option>
                    <option value="&#20891;&#20107;">Military</option>
                    <option value="&#31185;&#25216;">Technology</option>
                    <option value="&#25991;&#21270;">Culture</option>
                    <option value="&#32463;&#27982;">Economy</option>
                    <option value="&#31038;&#20250;">Society</option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Tags</label>
                  <input v-model="importMeta.tags" type="text" placeholder="tag1, tag2, tag3" class="cy-input" />
                </div>
                <div class="form-group">
                  <label>Importance (1-10)</label>
                  <input v-model.number="importMeta.importance" type="number" min="1" max="10" placeholder="5" class="cy-input" />
                </div>
              </div>
            </div>

            <div class="import-action-row">
              <button class="cy-btn cy-btn--gold" :disabled="!selectedFile || importing" @click="doImport">
                {{ importing ? 'Importing...' : 'Start Import' }}
              </button>
              <span class="import-inline-tip">Tip: set event and category first so later search feels cleaner.</span>
            </div>

            <div v-if="importResult" class="import-result" :class="importResult.imported > 0 ? 'success' : 'info'">
              <span>{{ importResult.imported > 0 ? 'OK' : 'i' }}</span>
              <span>Imported {{ importResult.imported }} chunks, skipped {{ importResult.skipped }} duplicates</span>
            </div>
          </div>

          <div class="section-block cy-card import-secondary-card">
            <div class="panel-header-row panel-header-row--stacked">
              <div>
                <h3 class="section-title">
                  <span class="section-icon">+</span>
                  Manual Entry
                </h3>
                <p class="import-hint">Use this panel for one-off notes, corrections, or small additions that do not come from files.</p>
              </div>
              <span class="manual-pill">Quick Add</span>
            </div>

            <div class="manual-form">
              <div class="form-group">
                <label>Title *</label>
                <input v-model="manualForm.title" type="text" placeholder="Entry title" class="cy-input" />
              </div>
              <div class="form-group">
                <label>Content *</label>
                <textarea v-model="manualForm.content" rows="7" placeholder="Entry content" class="cy-textarea" />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Event Name</label>
                  <input v-model="manualForm.event_name" type="text" placeholder="Linked event" class="cy-input" />
                </div>
                <div class="form-group">
                  <label>Year</label>
                  <input v-model.number="manualForm.year" type="number" placeholder="Year" class="cy-input" />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Region</label>
                  <select v-model="manualForm.region" class="cy-input">
                    <option value="">Any</option>
                    <option value="china">China</option>
                    <option value="foreign">Foreign</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Category</label>
                  <select v-model="manualForm.category" class="cy-input">
                    <option value="">Any</option>
                    <option value="&#25919;&#27835;">Politics</option>
                    <option value="&#20891;&#20107;">Military</option>
                    <option value="&#31185;&#25216;">Technology</option>
                    <option value="&#25991;&#21270;">Culture</option>
                    <option value="&#32463;&#27982;">Economy</option>
                    <option value="&#31038;&#20250;">Society</option>
                  </select>
                </div>
              </div>
              <button class="cy-btn cy-btn--cyan" :disabled="!manualForm.title || !manualForm.content || submitting" @click="doManualAdd">
                {{ submitting ? 'Submitting...' : 'Add Entry' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'browse'" class="tab-content">
        <div class="section-block cy-card search-drawer-card">
          <div class="drawer-head">
            <div class="drawer-head-copy">
              <h3 class="section-title">
                <span class="section-icon">*</span>
                Advanced Search
              </h3>
              <p class="import-hint">Open the drawer to combine region, category, year, importance, source, and status filters. Results stay visible below in every state.</p>
            </div>
            <button class="drawer-toggle" :class="{ open: searchDrawerOpen }" @click="toggleSearchDrawer">
              <span>{{ searchDrawerOpen ? 'Collapse filters' : 'Expand filters' }}</span>
              <strong>{{ activeBrowseFilterCount }} on</strong>
            </button>
          </div>

          <Transition name="drawer-slide">
            <div v-show="searchDrawerOpen" class="drawer-panel">
              <div class="conditional-filters conditional-filters--drawer">
                <div class="form-row">
                  <div class="form-group">
                    <label>Keyword</label>
                    <input v-model="condFilters.text" type="text" placeholder="Title / event / content keyword" class="cy-input" />
                  </div>
                  <div class="form-group">
                    <label>Event Name (fuzzy)</label>
                    <input v-model="condFilters.event_name_like" type="text" placeholder="e.g. Silk Road" class="cy-input" />
                  </div>
                </div>
                <div class="form-row form-row--triple">
                  <div class="form-group">
                    <label>Region</label>
                    <select v-model="condFilters.region" class="cy-input">
                      <option value="">Any</option>
                      <option value="china">China</option>
                      <option value="foreign">Foreign</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Category</label>
                    <select v-model="condFilters.category" class="cy-input">
                      <option value="">Any</option>
                      <option v-for="c in availableCategories" :key="c" :value="c">{{ c }}</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Source</label>
                    <select v-model="condFilters.source_type" class="cy-input">
                      <option value="">All sources</option>
                      <option value="file_import">File Import</option>
                      <option value="web_crawl">Web Crawl</option>
                      <option value="manual">Manual</option>
                      <option value="seed_data">Seed Data</option>
                    </select>
                  </div>
                </div>
                <div class="form-row form-row--triple">
                  <div class="form-group">
                    <label>Year From</label>
                    <input v-model.number="condFilters.year_min" type="number" placeholder="e.g. 0" class="cy-input" />
                  </div>
                  <div class="form-group">
                    <label>Year To</label>
                    <input v-model.number="condFilters.year_max" type="number" placeholder="e.g. 2000" class="cy-input" />
                  </div>
                  <div class="form-group">
                    <label>Min Importance</label>
                    <input v-model.number="condFilters.importance_min" type="number" min="1" max="10" placeholder="1-10" class="cy-input" />
                  </div>
                </div>
                <div class="form-row form-row--triple">
                  <div class="form-group">
                    <label>Tag</label>
                    <input v-model="condFilters.tag" type="text" placeholder="e.g. war" class="cy-input" />
                  </div>
                  <div class="form-group">
                    <label>Status</label>
                    <select v-model="condFilters.status" class="cy-input">
                      <option value="">All status</option>
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                      <option value="pending_review">Pending</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Sort</label>
                    <select v-model="condFilters.order_by" class="cy-input">
                      <option value="relevance">Relevance / Importance</option>
                      <option value="importance">Importance</option>
                      <option value="year">Year</option>
                      <option value="updated_at">Updated Time</option>
                    </select>
                  </div>
                </div>
                <div class="drawer-actions">
                  <button class="cy-btn cy-btn--cyan" @click="fetchEntries(1)">Run Search</button>
                  <button class="cy-btn cy-btn--ghost" @click="resetConditional">Reset</button>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <div class="section-block cy-card results-panel-card">
          <div class="results-panel-head">
            <div>
              <h3 class="section-title">
                <span class="section-icon">*</span>
                Knowledge Entries
              </h3>
              <p class="results-summary">{{ browseSummary }}</p>
            </div>
            <div class="results-panel-tools">
              <label class="inline-field">
                <span>Page Size</span>
                <select v-model.number="entriesPageSize" class="cy-input compact-select" @change="handleBrowsePageSizeChange">
                  <option v-for="size in browsePageSizeOptions" :key="size" :value="size">{{ size }}</option>
                </select>
              </label>
              <div v-if="conditionalResult" class="result-badge">{{ conditionalResult.total }} total</div>
            </div>
          </div>

          <div v-if="entriesLoading" class="loading-state">
            <div class="cy-loading"></div>
            <p>Loading...</p>
          </div>

          <div v-else-if="entries.length === 0" class="empty-state">
            <div class="empty-icon">o</div>
            <p>No entries found</p>
          </div>

          <div v-else class="entries-list">
            <div v-for="entry in entries" :key="entry.id" class="entry-card" @click="viewEntry(entry)">
              <div class="entry-head">
                <span class="entry-source-badge" :class="entry.source_type">
                  {{ sourceLabels[entry.source_type] || entry.source_type }}
                </span>
                <span class="entry-version">v{{ entry.version }}</span>
                <span v-if="entry.version_count && entry.version_count > 1" class="entry-version-total">
                  ({{ entry.version_count }} versions)
                </span>
                <span class="entry-status-badge" :class="entry.status">
                  {{ statusLabels[entry.status] || entry.status }}
                </span>
              </div>
              <h4 class="entry-title">{{ entry.title }}</h4>
              <p class="entry-preview">{{ entry.content_preview }}</p>
              <div class="entry-meta">
                <span v-if="entry.event_name" class="meta-item">Event {{ entry.event_name }}</span>
                <span v-if="entry.year" class="meta-item">Year {{ entry.year }}</span>
                <span v-if="entry.region" class="meta-item">{{ entry.region === 'china' ? 'China' : 'Foreign' }}</span>
                <span v-if="entry.category" class="meta-item">{{ entry.category }}</span>
                <span v-if="entry.tags && entry.tags.length" class="meta-item">{{ entry.tags.slice(0, 3).join(' / ') }}</span>
                <span v-if="entry.importance" class="meta-item">{{ entry.importance }}/10</span>
              </div>
              <div class="entry-footer">
                <span class="chunk-info">Chunk {{ entry.chunk_index + 1 }}/{{ entry.chunk_total }}</span>
                <span class="entry-date">{{ entry.created_at?.split('T')[0] || entry.created_at?.split(' ')[0] || '' }}</span>
                <button class="delete-btn" @click.stop="deleteEntry(entry.id)" title="Delete">x</button>
              </div>
            </div>
          </div>

          <div v-if="entriesTotal > 0" class="pagination pagination--panel">
            <div class="pagination-summary">
              <strong>{{ entriesTotal }}</strong>
              <span>results</span>
              <span>?</span>
              <span>{{ totalEntryPages }} pages</span>
            </div>
            <div class="pagination-controls">
              <button class="page-btn" :disabled="currentPage <= 1" @click="changeBrowsePage(currentPage - 1)">Previous</button>
              <span class="page-info">Page {{ currentPage }} / {{ totalEntryPages }}</span>
              <button class="page-btn" :disabled="currentPage >= totalEntryPages" @click="changeBrowsePage(currentPage + 1)">Next</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'sources'" class="tab-content">
        <div class="section-block cy-card">
          <div class="results-panel-head results-panel-head--sources">
            <div>
              <h3 class="section-title">
                <span class="section-icon">@</span>
                Crawl Sources
              </h3>
              <p class="import-hint">Long source lists are paged so the status panel stays compact and easier to scan.</p>
            </div>
            <div class="results-panel-tools">
              <label class="inline-field">
                <span>Page Size</span>
                <select v-model.number="sourcePageSize" class="cy-input compact-select" @change="handleSourcePageSizeChange">
                  <option v-for="size in sourcePageSizeOptions" :key="size" :value="size">{{ size }}</option>
                </select>
              </label>
              <div class="result-badge">{{ crawlSources.length }} total</div>
            </div>
          </div>
          <div v-if="crawlSources.length === 0" class="empty-state">
            <p>No sources available</p>
          </div>
          <div v-else class="crawl-sources-list">
            <div v-for="src in pagedCrawlSources" :key="src.id" class="crawl-source-card">
              <div class="crawl-source-head">
                <span class="crawl-source-name">{{ src.name }}</span>
                <span class="entry-status-badge" :class="src.last_status === 'success' ? 'active' : src.last_status === 'failed' ? 'archived' : 'pending_review'">
                  {{ src.last_status === 'success' ? 'Success' : src.last_status === 'failed' ? 'Failed' : 'Pending' }}
                </span>
                <span v-if="src.recommended" class="entry-source-badge seed_data">Recommended</span>
              </div>
              <a class="crawl-source-url" :href="src.url" target="_blank" rel="noopener">{{ src.url }}</a>
              <p v-if="src.description" class="crawl-source-desc">{{ src.description }}</p>
              <div class="crawl-source-meta">
                <span v-if="src.category">Category {{ src.category }}</span>
                <span v-if="src.region">Region {{ src.region === 'china' ? 'China' : src.region === 'foreign' ? 'Foreign' : src.region }}</span>
                <span v-if="src.last_imported !== null">Last import {{ src.last_imported }}</span>
                <span v-if="src.last_crawled_at">{{ src.last_crawled_at }}</span>
              </div>
              <div v-if="src.tags && src.tags.length" class="tag-list">
                <span v-for="tag in src.tags" :key="tag" class="tag-chip">{{ tag }}</span>
              </div>
            </div>
          </div>
          <div v-if="crawlSources.length > 0" class="pagination pagination--panel pagination--sources">
            <div class="pagination-summary">
              <strong>{{ crawlSources.length }}</strong>
              <span>sources</span>
              <span>?</span>
              <span>{{ totalSourcePages }} pages</span>
            </div>
            <div class="pagination-controls">
              <button class="page-btn" :disabled="sourceCurrentPage <= 1" @click="changeSourcePage(sourceCurrentPage - 1)">Previous</button>
              <span class="page-info">Page {{ sourceCurrentPage }} / {{ totalSourcePages }}</span>
              <button class="page-btn" :disabled="sourceCurrentPage >= totalSourcePages" @click="changeSourcePage(sourceCurrentPage + 1)">Next</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'detail' && selectedEntry" class="tab-content">
        <div class="section-block cy-card">
          <div class="detail-header">
            <button class="cy-btn cy-btn--ghost" @click="activeTab = 'browse'">Back to list</button>
            <div class="detail-actions">
              <button class="cy-btn cy-btn--ghost" :disabled="versionsLoading" @click="fetchVersions(selectedEntry.id)">
                {{ versionsLoading ? 'Loading...' : 'Version History' }}
              </button>
              <button class="cy-btn cy-btn--ghost" @click="deleteEntry(selectedEntry.id)">Delete</button>
            </div>
          </div>

          <div v-if="showVersions && entryVersions.length" class="version-history">
            <h4 class="version-history-title">Version History ({{ entryVersions.length }})</h4>
            <div class="version-list">
              <div v-for="v in entryVersions" :key="v.id" class="version-item">
                <div class="version-item-head">
                  <span class="version-num">v{{ v.version }}</span>
                  <span class="version-source-badge">{{ v.change_source || 'system' }}</span>
                  <span class="version-date">{{ v.created_at }}</span>
                </div>
                <div class="version-summary">{{ v.change_summary || 'No summary' }}</div>
                <div class="version-meta">
                  <span v-if="v.operator">Operator: {{ v.operator }}</span>
                  <span class="mono">hash: {{ v.content_hash?.substring(0, 12) }}...</span>
                </div>
                <div v-if="v.snapshot_meta" class="version-snapshot">
                  <details>
                    <summary>Snapshot metadata</summary>
                    <pre class="snapshot-pre">{{ JSON.stringify(v.snapshot_meta, null, 2) }}</pre>
                  </details>
                </div>
              </div>
            </div>
          </div>

          <h3 class="detail-title">{{ selectedEntry.title }}</h3>

          <div class="detail-meta-grid">
            <div class="meta-field">
              <span class="meta-label">Source</span>
              <span class="meta-value">{{ sourceLabels[selectedEntry.source_type] || selectedEntry.source_type }}</span>
            </div>
            <div class="meta-field">
              <span class="meta-label">Version</span>
              <span class="meta-value">v{{ selectedEntry.version }}</span>
            </div>
            <div class="meta-field">
              <span class="meta-label">Status</span>
              <span class="meta-value">{{ statusLabels[selectedEntry.status] || selectedEntry.status }}</span>
            </div>
            <div class="meta-field">
              <span class="meta-label">Chunk</span>
              <span class="meta-value">{{ selectedEntry.chunk_index + 1 }} / {{ selectedEntry.chunk_total }}</span>
            </div>
            <div v-if="selectedEntry.event_name" class="meta-field">
              <span class="meta-label">Event</span>
              <span class="meta-value">{{ selectedEntry.event_name }}</span>
            </div>
            <div v-if="selectedEntry.year" class="meta-field">
              <span class="meta-label">Year</span>
              <span class="meta-value">{{ selectedEntry.year < 0 ? 'BCE ' + Math.abs(selectedEntry.year) : 'CE ' + selectedEntry.year }}</span>
            </div>
            <div v-if="selectedEntry.region" class="meta-field">
              <span class="meta-label">Region</span>
              <span class="meta-value">{{ selectedEntry.region === 'china' ? 'China' : 'Foreign' }}</span>
            </div>
            <div v-if="selectedEntry.category" class="meta-field">
              <span class="meta-label">Category</span>
              <span class="meta-value">{{ selectedEntry.category }}</span>
            </div>
            <div v-if="selectedEntry.importance" class="meta-field">
              <span class="meta-label">Importance</span>
              <span class="meta-value">{{ selectedEntry.importance }}/10</span>
            </div>
            <div v-if="selectedEntry.source_url" class="meta-field meta-field--wide">
              <span class="meta-label">Source URL</span>
              <a class="meta-value link" :href="selectedEntry.source_url" target="_blank">{{ selectedEntry.source_url }}</a>
            </div>
            <div v-if="selectedEntry.file_name" class="meta-field">
              <span class="meta-label">File</span>
              <span class="meta-value">{{ selectedEntry.file_name }}</span>
            </div>
            <div v-if="selectedEntry.content_hash" class="meta-field meta-field--wide">
              <span class="meta-label">Content Hash</span>
              <span class="meta-value mono">{{ selectedEntry.content_hash?.substring(0, 16) }}...</span>
            </div>
            <div v-if="selectedEntry.tags && selectedEntry.tags.length" class="meta-field meta-field--wide">
              <span class="meta-label">Tags</span>
              <div class="tag-list">
                <span v-for="tag in selectedEntry.tags" :key="tag" class="tag-chip">{{ tag }}</span>
              </div>
            </div>
            <div v-if="selectedEntry.figures && selectedEntry.figures.length" class="meta-field meta-field--wide">
              <span class="meta-label">Figures</span>
              <div class="tag-list">
                <span v-for="fig in selectedEntry.figures" :key="fig" class="tag-chip figure">{{ fig }}</span>
              </div>
            </div>
          </div>

          <div class="detail-content">
            <h4 class="content-label">Content</h4>
            <div class="content-body">{{ selectedEntry.content }}</div>
          </div>

          <div class="detail-dates">
            <span>Created: {{ selectedEntry.created_at }}</span>
            <span>Updated: {{ selectedEntry.updated_at }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ragApi, type KnowledgeEntry, type KnowledgeStats, type KnowledgeVersion, type CrawlSource } from '@/api/rag'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const appStore = useAppStore()
const authStore = useAuthStore()
const router = useRouter()

if (!authStore.user?.is_admin) {
  try {
    appStore.showToast('warning', 'Admin access required for the knowledge base')
  } catch (_) {
    // app store unavailable
  }
  router.replace({ name: 'Home' })
}

const activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: 'Overview', icon: '[]' },
  { key: 'import', label: 'Import', icon: '+' },
  { key: 'browse', label: 'Browse', icon: '*' },
  { key: 'sources', label: 'Sources', icon: '@' },
]

const stats = reactive<KnowledgeStats>({
  total: 0, active: 0,
  by_source: {},
  by_region: {},
  latest_update: null,
})

const sourceLabels: Record<string, string> = {
  file_import: 'File Import',
  web_crawl: 'Web Crawl',
  manual: 'Manual',
  seed_data: 'Seed Data',
}

const availableCategories = computed(() => {
  const cats = new Set<string>()
  entries.value.forEach(e => { if (e.category) cats.add(e.category) })
  conditionalResult.value?.items?.forEach((e: any) => { if (e.category) cats.add(e.category) })
  return Array.from(cats).sort()
})

const statusLabels: Record<string, string> = {
  active: 'Active',
  archived: 'Archived',
  pending_review: 'Pending',
}

const crawling = ref(false)
const rebuilding = ref(false)
const seeding = ref(false)
const crawlSources = ref<CrawlSource[]>([])
const searchDrawerOpen = ref(true)
const sourceCurrentPage = ref(1)
const sourcePageSize = ref(6)
const entriesPageSize = ref(20)
const browsePageSizeOptions = [10, 20, 50, 100]
const sourcePageSizeOptions = [4, 6, 8, 12]
const BROWSE_DRAWER_STORAGE_KEY = 'kb_browse_drawer_open'

const condFilters = reactive({
  text: '',
  event_name_like: '',
  region: '',
  category: '',
  source_type: '',
  status: '',
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

const selectedEntry = ref<KnowledgeEntry | null>(null)

const totalEntryPages = computed(() => Math.max(1, Math.ceil(entriesTotal.value / entriesPageSize.value)))
const totalSourcePages = computed(() => Math.max(1, Math.ceil(crawlSources.value.length / sourcePageSize.value)))
const pagedCrawlSources = computed(() => {
  const start = (sourceCurrentPage.value - 1) * sourcePageSize.value
  return crawlSources.value.slice(start, start + sourcePageSize.value)
})
const activeBrowseFilterCount = computed(() => {
  const values = [
    condFilters.text,
    condFilters.event_name_like,
    condFilters.region,
    condFilters.category,
    condFilters.source_type,
    condFilters.status,
    condFilters.year_min,
    condFilters.year_max,
    condFilters.importance_min,
    condFilters.tag,
  ]
  return values.filter((value) => value !== '' && value !== undefined && value !== null).length
})
const browseSummary = computed(() => {
  if (entriesLoading.value) return 'Loading search results...'
  if (entriesTotal.value === 0) return 'No matching entries'
  const start = (currentPage.value - 1) * entriesPageSize.value + 1
  const end = Math.min(currentPage.value * entriesPageSize.value, entriesTotal.value)
  return `Showing ${start}-${end} of ${entriesTotal.value} entries, page ${currentPage.value} / ${totalEntryPages.value}`
})

function toggleSearchDrawer() {
  searchDrawerOpen.value = !searchDrawerOpen.value
  try {
    localStorage.setItem(BROWSE_DRAWER_STORAGE_KEY, String(searchDrawerOpen.value))
  } catch (_) {
    // ignore storage failure
  }
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
      const imported = res.data?.imported || 0
      const failed = res.data?.sources_failed || 0
      const processed = res.data?.sources_processed || 0
      if (processed > 0 && failed === processed) {
        appStore.showToast('error', `Crawl failed: ${failed}/${processed} sources failed`)
      } else if (failed > 0) {
        appStore.showToast('warning', `Crawl partially completed: imported ${imported}, failed ${failed}/${processed}`)
      } else {
        appStore.showToast('success', `Crawl completed: imported ${imported} entries`)
      }
      fetchStats()
      fetchCrawlSources()
    }
  } catch {
    appStore.showToast('error', 'Crawl failed')
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
        `Seed import completed: +${res.data?.imported || 0}, skipped ${res.data?.skipped || 0}, total ${res.data?.total_events || 0}`,
      )
      fetchStats()
    }
  } catch {
    appStore.showToast('error', 'Seed import failed')
  } finally {
    seeding.value = false
  }
}

async function fetchCrawlSources() {
  try {
    const res = await ragApi.listCrawlSources({ recommended: 1 })
    if (res.code === 200) {
      crawlSources.value = res.data?.items || []
      if (sourceCurrentPage.value > totalSourcePages.value) {
        sourceCurrentPage.value = totalSourcePages.value
      }
    }
  } catch { /* ignore */ }
}

async function doConditionalSearch(page = 1) {
  currentPage.value = page
  try {
    const res = await ragApi.conditionalSearch({
      text: condFilters.text || undefined,
      event_name_like: condFilters.event_name_like || undefined,
      region: condFilters.region || undefined,
      category: condFilters.category || undefined,
      source_type: condFilters.source_type || undefined,
      status: condFilters.status || undefined,
      year_min: condFilters.year_min,
      year_max: condFilters.year_max,
      importance_min: condFilters.importance_min,
      tag: condFilters.tag || undefined,
      order_by: condFilters.order_by,
      page_size: entriesPageSize.value,
      page: currentPage.value,
    })
    if (res.code === 200 && res.data) {
      conditionalResult.value = res.data
      entries.value = res.data.items || []
      entriesTotal.value = res.data.total || 0
    }
  } catch {
    appStore.showToast('error', 'Delete failed')
  }
}

function resetConditional() {
  condFilters.text = ''
  condFilters.event_name_like = ''
  condFilters.region = ''
  condFilters.category = ''
  condFilters.source_type = ''
  condFilters.status = ''
  condFilters.year_min = undefined
  condFilters.year_max = undefined
  condFilters.importance_min = undefined
  condFilters.tag = ''
  condFilters.order_by = 'relevance'
  condFilters.page_size = 20
  entriesPageSize.value = 20
  conditionalResult.value = null
  fetchEntries(1)
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
      appStore.showToast('success', 'Deleted successfully')
    }
  } catch {
    appStore.showToast('error', 'Delete failed')
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
      appStore.showToast('success', 'Deleted successfully')
      fetchStats()
      selectedFile.value = null
    }
  } catch {
    appStore.showToast('error', 'Delete failed')
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
      appStore.showToast('success', 'Deleted successfully')
      manualForm.title = ''
      manualForm.content = ''
      manualForm.event_name = ''
      fetchStats()
    }
  } catch {
    appStore.showToast('error', 'Delete failed')
  } finally {
    submitting.value = false
  }
}

async function fetchEntries(page = currentPage.value) {
  currentPage.value = page
  entriesLoading.value = true
  try {
    await doConditionalSearch(currentPage.value)
  } finally {
    entriesLoading.value = false
  }
}

function changeBrowsePage(page: number) {
  const target = Math.min(Math.max(page, 1), totalEntryPages.value)
  if (target === currentPage.value && entries.value.length > 0) return
  fetchEntries(target)
}

function handleBrowsePageSizeChange() {
  condFilters.page_size = entriesPageSize.value
  fetchEntries(1)
}

function changeSourcePage(page: number) {
  sourceCurrentPage.value = Math.min(Math.max(page, 1), totalSourcePages.value)
}

function handleSourcePageSizeChange() {
  sourceCurrentPage.value = 1
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
  if (!confirm('Delete this entry?')) return
  try {
    await ragApi.deleteEntry(id)
    appStore.showToast('success', 'Deleted successfully')
    fetchEntries()
    fetchStats()
    if (selectedEntry.value?.id === id) {
      selectedEntry.value = null
      activeTab.value = 'browse'
    }
  } catch {
    appStore.showToast('error', 'Delete failed')
  }
}

watch(activeTab, (tab) => {
  if (tab === 'overview') fetchStats()
  if (tab === 'browse') fetchEntries()
  if (tab === 'sources') fetchCrawlSources()
})

onMounted(() => {
  try {
    const savedDrawerState = localStorage.getItem(BROWSE_DRAWER_STORAGE_KEY)
    if (savedDrawerState !== null) {
      searchDrawerOpen.value = savedDrawerState === 'true'
    }
  } catch (_) {
    // ignore storage failure
  }
  condFilters.page_size = entriesPageSize.value
  fetchStats()
  fetchCrawlSources()
})
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

/* 闂備礁鎼崐鐟邦熆濮椻偓璺? 闂備礁鎼ˇ顐﹀焵椤掆偓瀵爼顢曢懞銉ょ箚妞ゆ劗鍠庢禍鍓х磽?*/
.conditional-filters { display: flex; flex-direction: column; gap: 8px; }

/* 闂備礁鎼崐鐟邦熆濮椻偓璺? 闂備胶绮悧顒勫礈濠靛棌鏋嶉柡鍥╁亹閺€?*/
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

/* 闂備礁鎼崐鐟邦熆濮椻偓璺? 闂備胶绮〃鍛存偋婵犲偊鑰垮ù鍏兼綑閸屻劑鏌涢埄鍐炬當闁?*/
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


.import-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.85fr);
  gap: 20px;
}

.import-primary-card,
.import-secondary-card,
.search-drawer-card,
.results-panel-card {
  position: relative;
}

.panel-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-header-row--stacked {
  flex-direction: column;
  align-items: stretch;
}

.import-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.import-chip,
.manual-pill,
.result-badge {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(49, 247, 255, 0.22);
  background: rgba(49, 247, 255, 0.08);
  color: var(--cyan-core);
  font-size: 11px;
  white-space: nowrap;
}

.selected-file--wide {
  justify-content: space-between;
}

.selected-file-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.import-action-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.import-inline-tip,
.results-summary {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
}

.kb-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(116px, 1fr));
  gap: 10px;
  padding: 14px 28px;
  background: rgba(8, 15, 28, 0.78);
  border-bottom: 1px solid var(--border-subtle);
}

.kb-tab {
  justify-content: center;
  min-height: 44px;
  padding: 10px 16px;
}

.tab-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-drawer-card {
  overflow: hidden;
}

.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.drawer-head-copy {
  min-width: 0;
}

.drawer-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: rgba(10, 18, 32, 0.9);
  color: var(--text-light);
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.drawer-toggle strong {
  color: var(--cyan-core);
  font-family: var(--font-mono);
  font-size: 12px;
}

.drawer-toggle.open {
  border-color: var(--border-cyan);
  box-shadow: 0 0 18px rgba(49, 247, 255, 0.12);
}

.drawer-panel {
  margin-top: 18px;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: all 0.28s ease;
  transform-origin: top center;
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.conditional-filters--drawer {
  gap: 12px;
}

.form-row--triple {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.drawer-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 4px;
}

.results-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.results-panel-tools {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.inline-field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.compact-select {
  min-width: 88px;
}

.pagination--panel {
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.pagination-summary,
.pagination-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pagination-summary {
  color: var(--text-muted);
  font-size: 12px;
}

.pagination-summary strong {
  color: var(--text-light);
  font-family: var(--font-mono);
}

.crawl-sources-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.results-panel-head--sources {
  margin-bottom: 18px;
}

@media (max-width: 960px) {
  .import-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .kb-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 10px 16px;
  }

  .drawer-head,
  .results-panel-head,
  .panel-header-row {
    flex-direction: column;
    align-items: stretch;
  }

  .form-row--triple {
    grid-template-columns: 1fr;
  }

  .pagination--panel {
    justify-content: center;
  }

  .results-panel-tools {
    justify-content: flex-start;
  }
}


@media (max-width: 640px) {
  .kb-header { padding: 12px 16px; gap: 12px; }
  .page-title { font-size: 16px; letter-spacing: 2px; }
  .kb-main { padding: 16px; }
  .form-row { grid-template-columns: 1fr; }
  .detail-meta-grid { grid-template-columns: 1fr; }
  .filter-select { width: 100%; }
}
</style>

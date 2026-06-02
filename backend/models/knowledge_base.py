import hashlib
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, JSON, DateTime,
    Index, UniqueConstraint, ForeignKey
)
from ..database import Base


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False, comment="事件/条目标题")
    content = Column(Text, nullable=False, comment="正文内容")
    content_hash = Column(String(64), nullable=False, comment="内容SHA256去重哈希")

    source_type = Column(String(32), nullable=False, default="manual", comment="来源: file_import/web_crawl/manual/seed_data")
    source_url = Column(String(512), nullable=True, comment="来源URL(爬虫)")
    file_name = Column(String(256), nullable=True, comment="导入文件名")
    file_type = Column(String(16), nullable=True, comment="文件类型: txt/md/csv/json/html")

    event_name = Column(String(256), nullable=True, comment="关联历史事件名称(去重主键)")
    year = Column(Integer, nullable=True, comment="事件年份(负数=公元前)")
    year_end = Column(Integer, nullable=True, comment="结束年份(时间段事件)")
    region = Column(String(32), nullable=True, comment="区域: china/foreign/other")
    importance = Column(Integer, nullable=True, comment="重要性 1-10")
    category = Column(String(64), nullable=True, comment="分类: 政治/军事/科技/文化/经济/社会")
    tags = Column(JSON, nullable=True, default=list, comment="标签列表")
    figures = Column(JSON, nullable=True, default=list, comment="相关人物")
    keywords = Column(JSON, nullable=True, default=list, comment="关键词列表(用于检索)")
    language = Column(String(16), nullable=True, default="zh-CN", comment="内容语言")
    source_reliability = Column(Integer, nullable=True, default=5, comment="来源可信度 1-10")

    chunk_index = Column(Integer, nullable=False, default=0, comment="文档分片索引(同一篇文档可能被拆成多个)")
    chunk_total = Column(Integer, nullable=False, default=1, comment="文档总分片数")

    version = Column(Integer, nullable=False, default=1, comment="当前版本号")
    latest_version_id = Column(Integer, nullable=True, comment="指向 KnowledgeVersion 的最新记录ID")
    version_count = Column(Integer, nullable=False, default=1, comment="已累计的版本总数")
    parent_event_id = Column(String(64), nullable=True, comment="来源原始事件ID(如 events_data 中的 id)")

    status = Column(String(16), nullable=False, default="active", comment="状态: active/archived/pending_review")
    is_locked = Column(Integer, nullable=False, default=0, comment="是否锁定: 0=否, 1=是")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_indexed_at = Column(DateTime, nullable=True, comment="最近一次RAG索引入库时间")

    __table_args__ = (
        UniqueConstraint("content_hash", "chunk_index", name="uq_knowledge_content_chunk"),
        UniqueConstraint("event_name", "chunk_index", "version", name="uq_knowledge_event_chunk_version"),
        Index("ix_knowledge_title", "title"),
        Index("ix_knowledge_event_name", "event_name"),
        Index("ix_knowledge_region", "region"),
        Index("ix_knowledge_source_type", "source_type"),
        Index("ix_knowledge_status", "status"),
        Index("ix_knowledge_year", "year"),
        Index("ix_knowledge_category", "category"),
        Index("ix_knowledge_importance", "importance"),
        Index("ix_knowledge_updated_at", "updated_at"),
        Index("ix_knowledge_event_region", "event_name", "region"),
        Index("ix_knowledge_region_year", "region", "year"),
        Index("ix_knowledge_category_region", "category", "region"),
    )

    @staticmethod
    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(Integer, ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False, comment="关联 KnowledgeEntry.id")
    version = Column(Integer, nullable=False, comment="版本号(自增)")
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    change_summary = Column(String(512), nullable=True, comment="版本变更说明")
    change_source = Column(String(32), nullable=True, comment="变更来源: file_import/web_crawl/manual_edit/auto_update")
    operator = Column(String(64), nullable=True, comment="操作者(用户标识/IP)")
    snapshot_meta = Column(JSON, nullable=True, default=dict, comment="变更时的完整元数据快照")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("entry_id", "version", name="uq_knowledge_version_entry_version"),
        Index("ix_knowledge_version_entry", "entry_id"),
        Index("ix_knowledge_version_created", "created_at"),
    )


class CrawlSource(Base):
    __tablename__ = "crawl_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, comment="来源名称(展示用)")
    url = Column(String(512), nullable=False, comment="来源URL")
    url_hash = Column(String(64), nullable=False, comment="URL的SHA256, 用于唯一约束避免长键")
    category = Column(String(64), nullable=True, comment="分类")
    region = Column(String(32), nullable=True, comment="区域")
    tags = Column(JSON, nullable=True, default=list, comment="标签列表")
    description = Column(String(512), nullable=True, comment="来源描述")
    recommended = Column(Integer, nullable=False, default=0, comment="是否为推荐来源: 0=否 1=是")
    enabled = Column(Integer, nullable=False, default=1, comment="是否启用: 0=否 1=是")
    priority = Column(Integer, nullable=False, default=5, comment="调度优先级 1-10, 越大越优先")
    last_crawled_at = Column(DateTime, nullable=True, comment="最近一次爬取时间")
    last_status = Column(String(16), nullable=True, default="pending", comment="最近一次爬取状态: success/failed/pending")
    last_imported = Column(Integer, nullable=True, default=0, comment="最近一次新导入条目数")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_crawl_source_url_hash"),
        Index("ix_crawl_source_enabled", "enabled"),
        Index("ix_crawl_source_priority", "priority"),
        Index("ix_crawl_source_recommended", "recommended"),
    )

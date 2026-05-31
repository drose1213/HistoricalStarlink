from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, Field, field_validator


# ==================== 基础响应模型 ====================

class BaseResponse(BaseModel):
    """统一响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[Any] = Field(default=None, description="响应数据")


class PaginationResponse(BaseModel):
    """分页响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[list] = Field(default=None, description="数据列表")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")


# ==================== 探索记录模型 ====================

class ExplorationRecordCreate(BaseModel):
    """创建探索记录请求"""
    session_id: str = Field(..., max_length=64, description="会话ID")
    event_id: str = Field(..., max_length=128, description="历史事件ID")
    event_name: str = Field(..., max_length=256, description="历史事件名称")
    event_year: Optional[int] = Field(default=None, description="事件年份")
    event_region: Optional[str] = Field(default=None, max_length=32, description="事件区域")
    parent_event_id: Optional[str] = Field(default=None, max_length=128, description="上级事件ID")
    depth: int = Field(default=0, ge=0, description="探索深度")
    explore_path: Optional[dict] = Field(default=None, description="完整探索路径")
    stay_duration: float = Field(default=0.0, ge=0, description="停留时长（秒）")
    from_direction: Optional[str] = Field(default=None, max_length=16, description="来源方向")


class ExplorationRecordQuery(BaseModel):
    """探索记录查询参数"""
    session_id: Optional[str] = Field(default=None, description="会话ID")
    event_id: Optional[str] = Field(default=None, description="历史事件ID")
    event_region: Optional[str] = Field(default=None, description="事件区域")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class ExplorationRecordOut(BaseModel):
    """探索记录输出"""
    id: int
    session_id: str
    event_id: str
    event_name: str
    event_year: Optional[int] = None
    event_region: Optional[str] = None
    parent_event_id: Optional[str] = None
    depth: int
    explore_path: Optional[dict] = None
    stay_duration: float
    from_direction: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 评分模型 ====================

class RatingCreate(BaseModel):
    """创建评分请求"""
    event_id: str = Field(..., max_length=128, description="历史事件ID")
    event_name: str = Field(..., max_length=256, description="历史事件名称")
    session_id: str = Field(..., max_length=64, description="会话ID")
    score: float = Field(..., ge=1.0, le=10.0, description="评分 1.0-10.0")
    comment: Optional[str] = Field(default=None, max_length=1000, description="评分备注")
    dimension_importance: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="重要性评分")
    dimension_interest: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="趣味性评分")
    dimension_impact: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="影响力评分")


class RatingUpdate(BaseModel):
    """更新评分请求"""
    score: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="评分")
    comment: Optional[str] = Field(default=None, max_length=1000, description="评分备注")
    dimension_importance: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="重要性评分")
    dimension_interest: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="趣味性评分")
    dimension_impact: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="影响力评分")


class RatingQuery(BaseModel):
    """评分查询参数"""
    event_id: Optional[str] = Field(default=None, description="历史事件ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    min_score: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="最低评分")
    max_score: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="最高评分")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class RatingStats(BaseModel):
    """评分统计"""
    event_id: str
    event_name: str
    avg_score: float
    count: int
    avg_importance: Optional[float] = None
    avg_interest: Optional[float] = None
    avg_impact: Optional[float] = None


class RatingOut(BaseModel):
    """评分输出"""
    id: int
    event_id: str
    event_name: str
    session_id: str
    score: float
    comment: Optional[str] = None
    dimension_importance: Optional[float] = None
    dimension_interest: Optional[float] = None
    dimension_impact: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 投票模型 ====================

class VoteCreate(BaseModel):
    """创建投票请求"""
    event_id: str = Field(..., max_length=128, description="历史事件ID")
    event_name: str = Field(..., max_length=256, description="历史事件名称")
    session_id: str = Field(..., max_length=64, description="会话ID")
    vote_type: int = Field(..., description="投票类型: 1=点赞, -1=踩")

    @field_validator("vote_type")
    @classmethod
    def validate_vote_type(cls, v):
        if v not in (1, -1):
            raise ValueError("投票类型只能是 1（赞）或 -1（踩）")
        return v


class VoteStats(BaseModel):
    """投票统计"""
    event_id: str
    event_name: str
    up_count: int = 0
    down_count: int = 0
    total: int = 0
    ratio: float = 0.0


class VoteOut(BaseModel):
    """投票输出"""
    id: int
    event_id: str
    event_name: str
    session_id: str
    vote_type: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 签名模型 ====================

class SignatureCreate(BaseModel):
    """创建签名记录（由文件上传接口内部使用）"""
    session_id: str = Field(..., max_length=64, description="会话ID")
    nickname: Optional[str] = Field(default=None, max_length=64, description="用户昵称")
    event_id: Optional[str] = Field(default=None, max_length=128, description="关联事件ID")
    context: Optional[str] = Field(default=None, max_length=500, description="附带文字")


class SignatureQuery(BaseModel):
    """签名查询参数"""
    session_id: Optional[str] = Field(default=None, description="会话ID")
    event_id: Optional[str] = Field(default=None, description="关联事件ID")
    is_approved: Optional[bool] = Field(default=None, description="审核状态")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class SignatureOut(BaseModel):
    """签名输出"""
    id: int
    session_id: str
    nickname: Optional[str] = None
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    file_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    event_id: Optional[str] = None
    context: Optional[str] = None
    is_approved: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 冠军卡片模型 ====================

class ChampionCardCreate(BaseModel):
    """创建冠军卡片请求"""
    session_id: str = Field(..., max_length=64, description="会话ID")
    nickname: Optional[str] = Field(default=None, max_length=64, description="用户昵称")
    event_id: str = Field(..., max_length=128, description="历史事件ID")
    event_name: str = Field(..., max_length=256, description="历史事件名称")
    event_year: Optional[int] = Field(default=None, description="事件年份")
    event_region: Optional[str] = Field(default=None, max_length=32, description="事件区域")
    event_description: Optional[str] = Field(default=None, description="事件描述")
    related_events: Optional[dict] = Field(default=None, description="关联事件数据")
    achievements: Optional[list] = Field(default=None, description="成就列表")


class ChampionCardUpdate(BaseModel):
    """更新冠军卡片请求"""
    nickname: Optional[str] = Field(default=None, max_length=64, description="用户昵称")
    is_favorite: Optional[bool] = Field(default=None, description="是否收藏")
    achievements: Optional[list] = Field(default=None, description="成就列表")


class ChampionCardQuery(BaseModel):
    """冠军卡片查询参数"""
    session_id: Optional[str] = Field(default=None, description="会话ID")
    event_id: Optional[str] = Field(default=None, description="历史事件ID")
    event_region: Optional[str] = Field(default=None, description="事件区域")
    card_level: Optional[int] = Field(default=None, description="卡片等级")
    is_favorite: Optional[bool] = Field(default=None, description="是否收藏")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class ChampionCardOut(BaseModel):
    """冠军卡片输出"""
    id: int
    session_id: str
    nickname: Optional[str] = None
    event_id: str
    event_name: str
    event_year: Optional[int] = None
    event_region: Optional[str] = None
    event_description: Optional[str] = None
    card_level: int
    explore_count: int
    total_stay_duration: float
    related_events: Optional[dict] = None
    achievements: Optional[list] = None
    is_favorite: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChampionCardStats(BaseModel):
    """冠军卡片统计"""
    session_id: str
    total_cards: int
    total_explores: int
    favorite_count: int
    level_distribution: dict

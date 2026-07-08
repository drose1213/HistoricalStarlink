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
    notes: Optional[str] = Field(default=None, max_length=1000, description="探索备注")
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
    notes: Optional[str] = None
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
    vote_type: int = Field(..., description="Vote type: 1=up, -1=down, 2=favorite")

    @field_validator("vote_type")
    @classmethod
    def validate_vote_type(cls, v):
        if v not in (1, -1, 2):
            raise ValueError("vote_type must be one of 1, -1, or 2")
        return v


class VoteStats(BaseModel):
    """投票统计"""
    event_id: str
    event_name: str
    up_count: int = 0
    down_count: int = 0
    favorite_count: int = 0
    star_count: int = 0
    my_vote: int = 0
    total: int = 0
    ratio: float = 0.0


class VoteOut(BaseModel):
    """投票输出 - 含最新三态计数与本会话投票状态"""
    id: int
    event_id: str
    event_name: str
    session_id: str
    vote_type: int
    created_at: Optional[datetime] = None
    # 扩展字段：投票后立即返回最新计数（spec rating-system-enhancement）
    agree_count: int = 0
    disagree_count: int = 0
    favorite_count: int = 0
    my_vote: int = 0  # current session vote: 1 / -1 / 2 / 0

    class Config:
        from_attributes = True


# ==================== 卡牌评价模型（spec rating-system-enhancement）====================

class CardReviewListItem(BaseModel):
    """评价列表项（含回复与点赞数）"""
    id: int
    card_id: Optional[int] = None
    auction_id: Optional[int] = None
    reviewer_session_id: str  # 原始 session_id（前端按需脱敏）
    stars: int
    comment: Optional[str] = None
    parent_review_id: Optional[int] = None
    likes_count: int = 0
    liked_by_me: bool = False
    reply_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CardReviewToggleLikeOut(BaseModel):
    """评价点赞 toggle 响应"""
    review_id: int
    liked: bool
    likes_count: int


class RatingDistributionItem(BaseModel):
    """评分分布 - 0-5 各星级数量"""
    stars: int  # 0-5
    count: int


class RatingTrendPoint(BaseModel):
    """评分趋势 - 单日平均分"""
    date: str  # YYYY-MM-DD
    avg_score: float
    count: int


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
    owner_session_id: Optional[str] = None
    is_on_auction: bool = False
    is_high_rated: bool = False
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


# ==================== 用户卡牌收藏模型 ====================

class UserCardCollectionCreate(BaseModel):
    """新增收藏请求"""
    user_session_id: str = Field(..., max_length=64, description="用户会话ID")
    card_id: int = Field(..., description="冠军卡牌ID")
    source: str = Field(default="explore", description="来源: explore/auction/system")


class UserCardCollectionOut(BaseModel):
    """用户卡牌收藏输出"""
    id: int
    user_session_id: str
    card_id: int
    event_id: str
    event_name: str
    is_high_rated: bool
    source: str
    collected_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 卡牌拍卖模型 ====================

class CardAuctionCreate(BaseModel):
    """上架拍卖请求"""
    card_id: int = Field(..., description="冠军卡牌ID")
    seller_session_id: str = Field(..., max_length=64, description="卖家会话ID")
    start_price: float = Field(..., ge=0, description="起拍价")
    min_increment: float = Field(default=5.0, ge=0, description="最小加价幅度")
    duration_hours: int = Field(default=24, ge=1, le=168, description="拍卖时长（小时）")
    description: Optional[str] = Field(default=None, max_length=500, description="拍卖描述")


class CardAuctionQuery(BaseModel):
    """拍卖列表查询"""
    status: Optional[str] = Field(default=None, description="状态过滤: active/sold/expired/cancelled")
    event_id: Optional[str] = Field(default=None, description="事件ID过滤")
    seller_session_id: Optional[str] = Field(default=None, description="卖家过滤")
    min_price: Optional[float] = Field(default=None, ge=0, description="最低当前价")
    max_price: Optional[float] = Field(default=None, ge=0, description="最高当前价")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class CardAuctionOut(BaseModel):
    """拍卖输出"""
    id: int
    card_id: int
    event_id: str
    event_name: str
    seller_session_id: str
    start_price: float
    current_price: float
    min_increment: float
    end_time: datetime
    status: str
    sold_price: Optional[float] = None
    platform_fee: Optional[float] = None
    seller_revenue: Optional[float] = None
    winner_session_id: Optional[str] = None
    description: Optional[str] = None
    bid_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 拍卖出价模型 ====================

class CardBidCreate(BaseModel):
    """出价请求"""
    auction_id: int = Field(..., description="拍卖ID")
    bidder_session_id: str = Field(..., max_length=64, description="出价者会话ID")
    amount: float = Field(..., gt=0, description="出价金额")


class CardBidOut(BaseModel):
    """出价输出"""
    id: int
    auction_id: int
    bidder_session_id: str
    amount: float
    is_winning: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 拍卖评价模型 ====================

class CardReviewCreate(BaseModel):
    """新增评价请求 - 支持拍卖评价或卡牌评价，可选回复父评价"""
    auction_id: Optional[int] = Field(default=None, description="拍卖ID（拍卖评价时使用）")
    card_id: Optional[int] = Field(default=None, description="卡牌ID（卡牌评价时使用）")
    reviewer_session_id: str = Field(..., max_length=64, description="评价者会话ID")
    stars: int = Field(..., ge=1, le=5, description="星级 1-5")
    comment: Optional[str] = Field(default=None, max_length=500, description="评价内容")
    parent_review_id: Optional[int] = Field(default=None, description="回复的父评价ID")

    @field_validator("comment")
    @classmethod
    def validate_content_length(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("评价内容不能超过 500 字")
        return v


class CardReviewOut(BaseModel):
    """评价输出"""
    id: int
    auction_id: Optional[int] = None
    card_id: Optional[int] = None
    reviewer_session_id: str
    stars: int
    comment: Optional[str] = None
    parent_review_id: Optional[int] = None
    likes_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

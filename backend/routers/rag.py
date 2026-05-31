"""
RAG API 路由 — 搜索相关事件 & RAG 问答
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ..schemas import BaseResponse
from ..rag_engine import search_similar, full_rag_query, build_index

router = APIRouter(prefix="/api/rag", tags=["RAG知识库"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")


class AskRequest(BaseModel):
    question: str = Field(..., description="用户问题")


@router.post("/search", response_model=BaseResponse, summary="搜索相关历史事件")
async def search_events(req: SearchRequest):
    results = await search_similar(req.query, top_k=req.top_k)
    events = []
    for item in results:
        ev = item["event"]
        events.append({
            "id": ev["id"],
            "name": ev["name"],
            "year": ev["year"],
            "region": ev["region"],
            "importance": ev["importance"],
            "description": ev["description"],
            "score": item["score"],
        })
    return BaseResponse(data=events)


@router.post("/ask", response_model=BaseResponse, summary="RAG 智能问答")
async def ask_question(req: AskRequest):
    result = await full_rag_query(req.question)
    return BaseResponse(data=result)


@router.post("/rebuild", response_model=BaseResponse, summary="重建 RAG 索引")
async def rebuild_index():
    info = await build_index()
    return BaseResponse(data=info)

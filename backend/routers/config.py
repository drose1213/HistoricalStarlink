import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.system_config import SystemConfig
from ..schemas import BaseResponse
from ..config import settings, load_db_config

logger = logging.getLogger("historical_starlink.config")

router = APIRouter(prefix="/api/config", tags=["系统配置"])


class ConfigItem(BaseModel):
    key: str
    value: Optional[str] = None
    group: str = "general"
    label: Optional[str] = None
    value_type: str = "string"


class ConfigUpdateRequest(BaseModel):
    configs: list[ConfigItem]


@router.get("", summary="获取所有配置")
async def get_configs(
    group: Optional[str] = Query(default=None, description="按分组筛选"),
    db: AsyncSession = Depends(get_db),
):
    query = select(SystemConfig)
    if group:
        query = query.where(SystemConfig.group == group)
    query = query.order_by(SystemConfig.group, SystemConfig.key)
    result = await db.execute(query)
    rows = result.scalars().all()
    data = [
        {
            "key": r.key,
            "value": r.value,
            "group": r.group,
            "label": r.label,
            "value_type": r.value_type,
        }
        for r in rows
    ]
    return BaseResponse(data=data)


@router.get("/groups", summary="获取所有配置分组")
async def get_config_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig.group).distinct())
    groups = [row[0] for row in result.all()]
    return BaseResponse(data=groups)


@router.get("/{key}", summary="获取单个配置")
async def get_config(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    row = result.scalar_one_or_none()
    if not row:
        return BaseResponse(code=404, message="配置不存在", data=None)
    return BaseResponse(data={
        "key": row.key,
        "value": row.value,
        "group": row.group,
        "label": row.label,
        "value_type": row.value_type,
    })


@router.put("", summary="更新配置（批量）")
async def update_configs(req: ConfigUpdateRequest, db: AsyncSession = Depends(get_db)):
    updated = 0
    for item in req.configs:
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == item.key)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value = item.value
            updated += 1
        else:
            db.add(SystemConfig(
                key=item.key,
                value=item.value,
                group=item.group,
                label=item.label,
                value_type=item.value_type,
            ))
            updated += 1
    await db.commit()

    await load_db_config()

    logger.info(f"Updated {updated} config items")
    return BaseResponse(message=f"成功更新 {updated} 项配置", data={"updated": updated})


@router.put("/{key}", summary="更新单个配置")
async def update_config(key: str, body: ConfigItem, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = body.value
    else:
        db.add(SystemConfig(
            key=key,
            value=body.value,
            group=body.group,
            label=body.label,
            value_type=body.value_type,
        ))
    await db.commit()
    await load_db_config()

    return BaseResponse(message="配置已更新")

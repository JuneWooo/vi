# -*- coding:utf-8 -*-
from fastapi import APIRouter
from app.api.endpoints import video_identify


api_router = APIRouter()
api_router.include_router(video_identify.router,
                          prefix="/video_identify", tags=["video_identify"])

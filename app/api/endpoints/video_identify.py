
from typing import List
from fastapi import File, UploadFile
from fastapi import APIRouter
from app.service.video_identify_service import video_identify_service
from app.api.resp import resp, RespStatus
from app.schemas.video_identify import VideoIdentify
from app.service.data_service import data_service
from app.schemas.video_data import UploadData
from sse_starlette import EventSourceResponse
from app.config.config import settings


router = APIRouter()


@router.post("/match_generate_data")
async def api_generate_stream(request: VideoIdentify):
    if not all([request.scenes, request.location, request.violation_category]):
        return resp(status_code=RespStatus.warning, msg="添加失败, scenes、location、violation_category 不能为空")

    # 创建一个 sse 响应
    return EventSourceResponse(
        video_identify_service.generate_stream_gate(request.scenes, request.location, request.violation_category))


@router.post("/upsert_data")
def api_upsert_data(request: UploadData):

    if not all([request.scenes, request.location, request.violation_category, request.measure]):
        return resp(status_code=RespStatus.warning, msg="scenes、location、violation_category、measure 不能为空")

    msg = data_service.upsert_data(request)

    if "success" in msg:
        return resp(status_code=RespStatus.success, msg=msg)
    else:
        return resp(status_code=RespStatus.error, msg=msg)


@router.post("/upload_embedding_docs")
async def api_upload_embedding(files: List[UploadFile] = File(...)):

    code, msg, data = data_service.upload_docs(
        files, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP_SIZE, settings.ZH_TITLE_ENHANCE)

    return resp(status_code=code, data=data, msg=msg)

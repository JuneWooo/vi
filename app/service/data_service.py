import time
from typing import Dict, Any, List, Tuple
from langchain_core.documents import Document
from fastapi import File, UploadFile, Form
from app import logger
from app.api.resp import RespStatus
from app.db.chroma import client
from app.db.chroma import MAPPING_COLLECTION, KNOWLEGE_BASE_COLLECTION
from app.db.chroma import get_langchain_chroma
from app.llms.tali_embedding import TaliAPIEmbeddings
from app.schemas.video_data import UploadData
from app.schemas.utils_chain import chain
from app.utils.str2md5 import md5GBK
from app.utils.save_files import _save_files_in_thread
from app.utils.spliter import files2docs_in_thread
from app.config.config import settings


embedding_function = TaliAPIEmbeddings()


class DataService:
    def upsert(self, content: str, doc_id: str, doc_info: Dict[str, Any], request: UploadData) -> str:
        mc = get_langchain_chroma(MAPPING_COLLECTION)
        # 不存在插入

        if not doc_info["documents"]:
            doc = Document(
                page_content=content,
                metadata={
                    "scenes": request.scenes,
                    "location": request.location,
                    "violation_category": request.violation_category,
                    "measure": request.measure,
                    "element": request.element if request.element else "",
                    "category": request.category if request.category else "",
                    "desc": content,
                    "basis_measure": request.basis_measure if request.basis_measure else "",
                    "source": "sidss platform create"
                }
            )
            try:
                mc.from_documents(
                    ids=[doc_id],
                    documents=[doc],
                    collection_name=f"{MAPPING_COLLECTION.name}",
                    embedding=embedding_function,
                    client=client,
                    relevance_score_fn=lambda distance: 1.0 - distance / 2
                )
                logger.info(
                    f"添加 {content} 完成 ===> Collection:{MAPPING_COLLECTION.name}")
            except Exception as e:
                logger.warning(f"记录插入时发生异常:{e}")
                msg = f"insert failed:{e}"
            else:
                msg = "insert success"
        # 存在，更新
        elif doc_info["documents"]:
            try:
                mc.update_document(doc_id, Document(
                    page_content=content,
                    metadata={
                        "scenes": request.scenes if request.scenes else doc_info["metadatas"][0]["scenes"],
                        "location": request.location if request.location else doc_info["metadatas"][0]["location"],
                        "violation_category": request.violation_category if request.violation_category else doc_info[
                            "metadatas"][0]["violation_category"],
                        "measure": request.measure if request.measure else doc_info["metadatas"][0]["measure"],
                        "element": request.element if request.element else doc_info[
                                "metadatas"][0]["element"],
                        "category": request.category if request.category else doc_info[
                                "metadatas"][0]["category"],
                        "desc": request.desc if request.desc else doc_info["metadatas"][0]["desc"],
                        "basis_measure": request.basis_measure if request.basis_measure else doc_info[
                                "metadatas"][0]["basis_measure"],
                        "source": "sidss platform update"
                    })
                )
            except Exception as e:
                logger.warning(f"记录更新时发生异常:{e}")
                msg = f"update failed:{e}"
            else:
                logger.info(
                    f"违规类别 {content} 已更新 ===> Collection:{MAPPING_COLLECTION.name}")
                msg = "update success"
        else:
            logger.info(f"data_info documents is empty")
            msg = f"error"

        return msg

    def upsert_data(self, request: UploadData) -> str:
        content = chain.invoke({
            "scenes": request.scenes,
            "location": request.location,
            "violation_category": request.violation_category
        })
        doc_id = md5GBK(
            "".join([request.scenes, request.location, request.violation_category]))

        doc_info = get_langchain_chroma(MAPPING_COLLECTION).get(ids=[doc_id])

        msg = self.upsert(content, doc_id, doc_info, request)

        return msg

    def upload_docs(self,
                    files: List[UploadFile] = File(...,
                                                   description="上传文件，支持多文件"),
                    chunk_size: int = Form(
                        settings.CHUNK_SIZE, description="知识库中单段文本最大长度"),
                    chunk_overlap: int = Form(
                        settings.CHUNK_OVERLAP_SIZE, description="知识库中相邻文本重合长度"),
                    zh_title_enhance: bool = Form(
                        settings.ZH_TITLE_ENHANCE, description="是否开启中文标题加强")
                    ) -> Tuple[int, str, Dict[str, Any]]:
        failed_files = {}
        file_names = []

        # 运行时间计算
        start_time = time.time()
        logger.info("开始上传文档!")
        # 文件保存到磁盘
        for result in _save_files_in_thread(files):
            filename = result["data"]["file_name"]
            if result["code"] != RespStatus.success:
                failed_files[filename] = result["msg"]

            if filename not in file_names:
                file_names.append(filename)
        execution_time = time.time() - start_time
        logger.info(f"上传文档完成! 耗时:{execution_time}s")

        s_time = time.time()
        logger.info("开始文档分块、向量化处理！")
        # 多线程分块、 然后向量化
        for status, result in files2docs_in_thread(
                file_names,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                zh_title_enhance=zh_title_enhance):

            if status:
                file_name, splited_docs = result
                knowlege_base = get_langchain_chroma(KNOWLEGE_BASE_COLLECTION)
                try:
                    knowlege_base.from_documents(
                        documents=splited_docs,
                        collection_name=f"{KNOWLEGE_BASE_COLLECTION.name}",
                        embedding=embedding_function,
                        client=client
                    )
                except Exception as e:
                    msg = f"文件：{file_name}向量化失败: {e}"
                    failed_files[file_name] = msg
            else:
                file_name, error = result
                failed_files[file_name] = error

        e_time = time.time() - s_time
        logger.info(f"分块、向量化完成，耗时：{e_time}s")

        return RespStatus.success, "文件上传与向量化完成", {"失败文件": failed_files}


data_service = DataService()

import os
from fastapi import UploadFile
from typing import List
from app import logger
from app.api.resp import RespStatus
from app.utils.run_in_thread import run_in_thread_pool


def _save_files_in_thread(files: List[UploadFile]):
    """
    通过多线程将上传的文件保存到对应知识库目录内。
    生成器返回保存结果：{"code":200, "msg": "xxx", "data": {"file_name": "xxx"}}
    """

    def save_file(file: UploadFile) -> dict:
        '''
        保存单个文件。
        '''
        try:
            filename = file.filename
            file_path = os.path.join("app/static/docs/", file.filename)
            data = {"file_name": filename}

            file_content = file.file.read()  # 读取上传文件的内容
            if (os.path.isfile(file_path) and os.path.getsize(file_path) == len(file_content)
                ):
                file_status = f"文件 {filename} 已存在。"
                logger.warning(file_status)
                return dict(code=RespStatus.error, msg=file_status, data=data)

            suffix = "pdf", "doc", "docx"
            if not filename.endswith(suffix):
                file_status = f"文件上传失败，仅支持PDF、Word、Excel格式文件"
                logger.warning(file_status)
                return dict(code=RespStatus.noAuth, msg=file_status, data=data)

            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "wb") as f:
                f.write(file_content)
            return dict(code=RespStatus.success, msg=f"成功上传文件 {filename}", data=data)
        except Exception as e:
            msg = f"{filename} 文件上传失败，报错信息为: {e}"
            logger.error(msg)
            return dict(code=RespStatus.error, msg=msg, data=data)

    params = [{"file": file} for file in files]
    for result in run_in_thread_pool(save_file, params=params):
        yield result

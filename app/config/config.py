# -*- coding:utf-8 -*-
"""
@file: config.py
@author: June
@date: 2024/3/1
@IDE: vscode
"""
from pydantic import BaseSettings
from pydantic import AnyHttpUrl
from typing import List


class Setting(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    

    PROJECT_NAME: str = "VI"
    DESCRIPTION: str = "VideoIdentify"

    # api
    API_V1_STR: str = "/api"
    IS_DEV: bool

    # log
    LOG_DIR: str = "logs/video_test{time}.log"
    LOG_LEVEL: str

    # Chroma
    CHROMA_HOST: str
    CHROMA_PORT: int

    # LLM
    LLM_HOST: str
    LLM_PORT: int

    # EMBEDDING
    EMBEDDING_HOST: str
    EMBEDDING_PORT: int

    # VECTOR SCORE
    SCORE: float

    # File Path
    FILE_PATH: str = "app/static/docs"

    ZH_TITLE_ENHANCE: bool  # ZH_TITLE_ENHANCE 中文标题加强
    CHUNK_SIZE: int
    CHUNK_OVERLAP_SIZE: int

    OPEN_CROSS_DOMAIN: bool  # 跨域


settings = Setting()

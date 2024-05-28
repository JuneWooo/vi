import os
import re
from typing import List, Generator, Tuple
from fastapi import File, UploadFile
from datetime import datetime
from app import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config.config import settings
from app.utils.zh_title_enhance import func_zh_title_enhance
from app.utils.run_in_thread import run_in_thread_pool


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def _split_text_with_regex_from_end(
        text: str, separator: str, keep_separator: bool
):
    # Now that we have the separator, split the text
    if separator:
        if keep_separator:
            # The parentheses in the pattern keep the delimiters in the result.
            _splits = re.split(f"({separator})", text)
            splits = ["".join(i) for i in zip(_splits[0::2], _splits[1::2])]
            if len(_splits) % 2 == 1:
                splits += _splits[-1:]
            # splits = [_splits[0]] + splits
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s != ""]


class ChineseRecursiveTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(
            self,
            separators=None,
            keep_separator: bool = True,
            is_separator_regex: bool = True,
            **kwargs,
    ) -> None:
        """Create a new TextSplitter."""
        super().__init__(keep_separator=keep_separator, **kwargs)
        self._separators = separators or [
            # r"第[\u4e00-\u9fa5]+条\s+|第[\u4e00-\u9fa5]+款\s+|第[\u4e00-\u9fa5]+号\s+|第[\u4e00-\u9fa5]+项\s+|第[\u4e00-\u9fa5]+章\s+|第[\u4e00-\u9fa5]+节\s+",
            # r"第\d+条\s+|第\d+款\s+|第\d+号\s+|第\d+项\s+|第\d+章\s+|第\d+节\s+",
            "\n\n",
            "\n",
            "。|！|？",
            "\.\s|\!\s|\?\s",
            "；|;\s",
            "，|,\s"
        ]
        self._is_separator_regex = is_separator_regex

    def _split_text(self, text: str, separators):
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self._is_separator_regex else re.escape(_s)
            if _s == "":
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1:]
                break

        _separator = separator if self._is_separator_regex else re.escape(
            separator)
        splits = _split_text_with_regex_from_end(
            text, _separator, self._keep_separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        _separator = "" if self._keep_separator else separator
        for s in splits:
            if self._length_function(s) < self._chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return [re.sub(r"\n{2,}", "\n", chunk.strip()) for chunk in final_chunks if chunk.strip()!=""]

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self._separators)


def file2text(
    file_name: str,
    chunk_size: int,
    chunk_overlap: int,
    zh_title_enhance: bool
) -> List[Document]:
    file_path = os.path.join("app/static/docs/", file_name)
    if file_name.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_name.endswith(".docx") or file_name.endswith(".doc"):
        loader = Docx2txtLoader(file_path)
    else:
        msg = f"文件类型不在Loader支持的范围中: ['pdf, docx']"
        logger.error(msg)
        return False, (file_name, msg)

    docs = loader.load()
    # 分割
    text_splitter = ChineseRecursiveTextSplitter(
        keep_separator=True,
        is_separator_regex=True,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    texts = ""
    for doc in docs:
        texts += doc.page_content

    split_docs = text_splitter.split_text(texts)

    createday = datetime.now()

    splited_docs = []
    for doc in split_docs:
        splited_docs.append(Document(page_content=doc, metadata={
            "source": docs[0].metadata["source"],
            "created_at": createday.strftime("%Y-%m-%d %H:%M:%S")
        }))

    logger.warning(f"原始分块个数：{len(splited_docs)}")
    if zh_title_enhance:
        splited_docs = func_zh_title_enhance(splited_docs)

    logger.warning(f"中文标题加强分割后个数{len(splited_docs)}")

    return splited_docs


def files2docs_in_thread(upload_files: List[str], chunk_size: int, chunk_overlap: int, zh_title_enhance: bool) -> Generator:
    '''
    利用多线程批量将磁盘文件转化成langchain Document.
    如果传入参数是Tuple，形式为(filename, kb_name)
    生成器返回值为 status, (kb_name, file_name, docs | error)
    '''

    def file2docs(**kwargs) -> Tuple[bool, Tuple[str, str, List[Document]]]:
        try:
            return True, (kwargs['file_name'], file2text(**kwargs))
        except Exception as e:
            msg = f"{kwargs['file_name']}加载文档时出错：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}')
            return False, (kwargs['file_name'], msg)

    kwargs_list = []
    for i, file_name in enumerate(upload_files):
        kwargs = {}
        kwargs["file_name"] = file_name
        kwargs["chunk_size"] = chunk_size
        kwargs["chunk_overlap"] = chunk_overlap
        kwargs["zh_title_enhance"] = zh_title_enhance

        kwargs_list.append(kwargs)

    for result in run_in_thread_pool(func=file2docs, params=kwargs_list):
        yield result

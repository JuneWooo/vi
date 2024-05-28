from typing import List, Dict, Tuple
from pandas.core.frame import DataFrame
import os
import pandas as pd
import json
import requests
from app.llms.tali_llm import TaliLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
import chromadb
# from chromadb.config import Settings
from app.llms.tali_embedding import TaliAPIEmbeddings
from langchain_community.vectorstores.chroma import Chroma


client = chromadb.HttpClient(
    host="localhost",
    port=8000
)


embedding_function = TaliAPIEmbeddings()

SCENES_COLLECTION = Chroma(collection_name="bz_scenes_doc",
                           client=client, embedding_function=embedding_function)
LOCATION_COLLECTION = Chroma(collection_name="bz_location_doc",
                             client=client, embedding_function=embedding_function)
VIOLATION_CATEGORY_COLLECTION = Chroma(
    collection_name="bz_violation_category_doc", client=client, embedding_function=embedding_function)


def send_info(pdata: DataFrame) -> Dict[str, list]:
    match_info = {
        "位置": [],
    }

    for i, row in pdata.iterrows():
        vac_doc = VIOLATION_CATEGORY_COLLECTION.get(
            where={"value": row["现场处理措施"]})
        if len(vac_doc.get("metadatas")) == 1:
            if row["场景"] in vac_doc.get("metadatas")[0]["source"]:
                match_info["位置"].append(vac_doc.get("metadatas")[0]["source"].split("+")[-1])
            else:
                match_info["位置"].append(None)
        else:
            res = []
            for vac_info in vac_doc.get("metadatas"):
                if row["场景"] in vac_info["source"] and vac_info["source"].split("+")[-1] not in res:
                    res.append(vac_info["source"].split("+")[-1])
                    break
            if res:
                match_info["位置"].append(res[0])
            else:
                match_info["位置"].append(None)
                
    return match_info


def compare(file_path:str, sname:str) -> Dict[str, list]:

    pdata = pd.read_excel(file_path, sheet_name=sname,
                          usecols="A,E,G", engine='openpyxl')
    match_info = send_info(pdata)

    return match_info


def main(file_path: str) -> None:
    original_data_1 = pd.read_excel(file_path, sheet_name="人员行为及装备规范")
    match_person_info = compare(file_path, sname="人员行为及装备规范")
    original_data_1.insert(1, "位置", match_person_info["位置"])
    original_data_1.to_excel('app/static/BZ应急素材梳理（矿山三+位置）-v2.xlsx', index=False, sheet_name="人员行为及装备规范")

    # original_data_2 = pd.read_excel(file_path, sheet_name="车辆分类及规范")
    # match_car_info = compare(file_path, sname="车辆分类及规范")
    # original_data_2.insert(1, "位置", match_car_info["位置"])
    # original_data_2.to_excel('app/static/BZ应急素材梳理（矿山三+位置）-v2.xlsx', index=False, sheet_name="车辆分类及规范")
    
    # original_data_3 = pd.read_excel(file_path, sheet_name="设备状态规范")
    # match_bot_info = compare(file_path, sname="设备状态规范")
    # original_data_3.insert(1, "位置", match_bot_info["位置"])
    # original_data_3.to_excel('app/static/BZ应急素材梳理（矿山三+位置）-v2.xlsx', index=False, sheet_name="设备状态规范")

    # original_data_4 = pd.read_excel(file_path, sheet_name="环境状态及规范")
    # match_env_info = compare(file_path, sname="环境状态及规范")
    # original_data_4.insert(1, "位置", match_env_info["位置"])
    # original_data_4.to_excel('app/static/BZ应急素材梳理（矿山三+位置）-v2.xlsx', index=False, sheet_name="环境状态及规范")
    
    print("插入完成！")


if __name__ == "__main__":
    file_path = f"app/static/BZ应急素材梳理（矿山三）-v2.xlsx"
    main(file_path)

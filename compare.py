from typing import List, Dict, Tuple
from pandas.core.frame import DataFrame
import os
import pandas as pd
import json

from tqdm import tqdm
import requests
from app.llms.tali_llm import TaliLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime

model = TaliLLM()
parser = StrOutputParser()

# compare_prompt = ChatPromptTemplate.from_template(
#     "你的任务是对输入的两段文本进行语义相似度计算，请对比`文本1`：{text1}和`文本2`：{text2}语义之间的相似度，最后给出一个范围\
#     在0-1之间的评分，评分要有说服力不能胡编乱造，最后只返回评分，不要其他说明信息。注意：如果`文本1`是空值则最后评分只返回0.0。"
# )
compare_prompt = ChatPromptTemplate.from_template(
    """
你的任务是对输入的文本1和文本2给出语义相似度评分，评分在0-1之间，评分要有说服力不能胡编乱造。
示例:
###
    文本1：严格按机电管理制度执行，加强违章人员教育
    文本2：None
    评分：0.0

    文本1：及时清理摄像头
    文本2：清理摄像头
    评分：0.8

    文本1：及时清理摄像头
    文本2：及时清理摄像头
    评分：1.0
###
最后只返回评分分值，不要输出示例（`###`之间的内容）和其他的说明信息。    
文本1：{text1}
文本2：{text2}
评分：
"""
)

compare_chain = compare_prompt | model | parser
time_str = str(datetime.today().year) + "_" +\
    str(datetime.today().month) + \
    "_" + str(datetime.today().day)


def send_info(pdata: DataFrame) -> Dict[str, list]:
    headers = {'Content-type': 'application/json'}
    training_info = {
        "场景（训练）": [],
        "位置（训练）": [],
        "要素（训练）": [],
        "类别（训练）": [],
        "违规类别（训练）": [],
        "违法行为描述（训练）": [],
        "现场处理措施（训练）": [],
        "相关率": []
    }

    for i, row in pdata.iterrows():
        pdata_list = []
        pdict = {}
        if row.get("场景"):
            pdict["scenes"] = row["场景"]
        if row.get("位置"):
            pdict["location"] = row["位置"]
        if row.get("违规类别"):
            pdict["violation_category"] = row["违规类别"]
        pdata_list.append(pdict)

        try:
            resp = requests.post(
                url="http://127.0.0.1:8001/api/video_identify/match_generate_data", headers=headers, data=json.dumps(pdata_list), timeout=60.0)

            result = json.loads(resp.text)['result'][0]
            training_info["场景（训练）"].append(result["scenes"])
            training_info["位置（训练）"].append(result["location"])
            training_info["违规类别（训练）"].append(
                result["violation_category"])
            training_info["要素（训练）"].append(result["element"])
            training_info["类别（训练）"].append(result["category"])
            training_info["违法行为描述（训练）"].append(result["desc"])
            training_info["现场处理措施（训练）"].append(result["measure"])
            rate = compare_chain.invoke(
                {
                    "text1": row["现场处理措施"],
                    "text2": result["measure"]
                }
            )
            if result["measure"] in ["", None] and rate != "0.0":
                rate = "0.0"
            training_info["相关率"].append(rate)

        except Exception as e:

            training_info["场景（训练）"].append(None)
            training_info["位置（训练）"].append(None)
            training_info["违规类别（训练）"].append(None)
            training_info["要素（训练）"].append(None)
            training_info["类别（训练）"].append(None)
            training_info["违法行为描述（训练）"].append(None)
            training_info["现场处理措施（训练）"].append(None)
            rate = "0.0"
            training_info["相关率"].append(rate)
            print(f"请求发生异常{e}")
            continue

    return training_info


def compare(file_path, sheet_name) -> Dict[str, list]:

    pdata = pd.read_excel(file_path, sheet_name=sheet_name,
                          usecols="C,D,H,J", engine='openpyxl')
    training_info = send_info(pdata)

    return training_info


def main(file_path, sheet_name) -> None:

    training_info = compare(file_path, sheet_name)
    # original_data = pd.read_excel(file_path, sheet_name="梳理表0131")
    original_data = pd.read_excel(file_path, sheet_name)

    col_idx = len(original_data.columns)
    original_data.insert(col_idx, "场景（训练）", training_info["场景（训练）"])
    original_data.insert(col_idx+1, "位置（训练）", training_info["位置（训练）"])
    original_data.insert(col_idx+2, "要素（训练）", training_info["要素（训练）"])
    original_data.insert(col_idx+3, "类别（训练）", training_info["类别（训练）"])
    original_data.insert(col_idx+4, "违规类别（训练）", training_info["违规类别（训练）"])
    original_data.insert(col_idx+5, "违法行为描述（训练）", training_info["违法行为描述（训练）"])
    original_data.insert(col_idx+6, "匹配值（处理措施）", training_info["现场处理措施（训练）"])
    original_data.insert(col_idx+7, "相关率", training_info["相关率"])

    original_data.to_excel('app/static/BZ应急素材梳理（评估）.xlsx',
                           sheet_name=sheet_name, index=False)
    print("对比完成！")


if __name__ == "__main__":
    file_path = f"app/static/BZ应急素材梳理.xlsx"
    # sheet_list = ["人员行为及装备规范", "车辆分类及规范", "设备状态规范", "环境状态及规范"]
    # for sname in sheet_list:
    main(file_path, sheet_name="梳理表0131")

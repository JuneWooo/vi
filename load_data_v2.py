import pandas as pd
import numpy as np
import json
import requests


class RequestDataError(Exception):
    pass


na = np.nan
headers = {'Content-type': 'application/json'}


def insert(file_path, sheet_name):
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    for index, row in data.iterrows():
        pdict = {}
        pdict["scenes"] = row["场景"]
        pdict["location"] = row["位置"]
        pdict["violation_category"] = row["违规类别"]
        pdict["element"] = row["要素"]
        pdict["category"] = row["类别"]
        pdict["desc"] = row["违法行为描述"]
        if type(row["违法行为描述"]) == float:
            pdict["desc"] = None
        pdict["measure"] = row["现场处理措施"]
        if row.get("现场处理依据"):
            pdict["basis_measure"] = row["现场处理依据"]
            if type(row["现场处理依据"]) == float:
                pdict["basis_measure"] = None

        try:
            resp = requests.post(
                url="http://192.168.11.190:8003/api/video_identify/upsert_data", headers=headers, data=json.dumps(pdict))
            print("请求结束：", resp.status_code)
            if resp.status_code != 200:
                raise RequestDataError()
        except Exception as e:
            print(f"请求发生异常{e}")
            continue
        else:
            print(f'{row["场景"]}-{row["位置"]}-{row["违规类别"]}插入成功')

    print(f"{sheet_name}插入完成")


def main(file_path):
    sheet_list = ["人员行为及装备规范", "车辆分类及规范", "设备状态规范", "环境状态及规范"]
    for sheet in sheet_list:
        insert(file_path=file_path, sheet_name=sheet)


if __name__ == "__main__":
    file_path = f"app/static/docs/矿山三违场景梳理汇总v2.xlsx"
    main(file_path)

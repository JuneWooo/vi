# -*- coding:utf-8 -*-

from typing import List
import pandas as pd
from langchain_core.documents import Document


def extra_data(file_path):
    """
    excel 数据存入 chroma vector
    Returns:

    """
    scenes = []
    location = []
    violation_category = []
    scenes_result = []
    location_result = []
    violation_category_result = []
    # 读取 excel
    data = pd.read_excel(file_path, sheet_name="梳理表0131(yanglong)")
    # 去重
    data.drop_duplicates(subset=["场景", "位置", "违规类别", "现场处理措施"], inplace=True)
    # 转为树 dict
    for index, row in data.iterrows():
        # print(row["场景"])
        # break
        if type(row["违法行为描述"]) in [float, int]:
            row["违法行为描述"] = ""
        if type(row["违规类别"]) in [float]:
            continue
        try:
            if "\n" in row["场景"]:
                row["场景"] = row["场景"].replace("\n", "")
            if "\n" in row["位置"]:
                row["位置"] = row["位置"].replace("\n", "")
            if "\n" in row["违规类别"]:
                row["违规类别"] = row["违规类别"].replace("\n", "")
            if "\n" in row["违法行为描述"]:
                row["违法行为描述"] = row["违法行为描述"].replace("\n", "")
            if "\n" in row["现场处理措施"]:
                row["现场处理措施"] = row["现场处理措施"].replace("\n", "")
        except Exception:
            import pdb;pdb.set_trace()

        if f'{row["场景"]}' not in scenes:
            # 场景未写入，插入全部数据
            scenes_result.append(Document(page_content=row["场景"]))
            location_result.append(
                Document(page_content=row["位置"], metadata={"source": row["场景"]}))
            violation_category_result.append(
                Document(page_content=row["违规类别"], metadata={"local": f'{row["位置"]}', "measure": row["现场处理措施"], "desc": row["违法行为描述"]}))

            scenes.append(f'{row["场景"]}')
            location.append(f'{row["场景"]}{row["位置"]}')
            violation_category.append(f'{row["场景"]}{row["位置"]}{row["违规类别"]}')

        elif f'{row["场景"]}{row["位置"]}' not in location:
            # 场景+位置 未写入，插入位置 之后的数据
            location_result.append(
                Document(page_content=row["位置"], metadata={"source": row["场景"]}))
            violation_category_result.append(
                Document(page_content=row["违规类别"], metadata={"local": f'{row["位置"]}', "measure": row["现场处理措施"], "desc": row["违法行为描述"]}))
            location.append(f'{row["场景"]}{row["位置"]}')
            violation_category.append(f'{row["场景"]}{row["位置"]}{row["违规类别"]}')

        elif f'{row["场景"]}{row["位置"]}{row["违规类别"]}' not in violation_category:
            # 场景+位置+违规类别 未写入，插入 违规类别 之后的数据
            violation_category_result.append(
                Document(page_content=row["违规类别"],
                         metadata={"local": f'{row["位置"]}', "measure": row["现场处理措施"], "desc": row["违法行为描述"]}))
            violation_category.append(f'{row["场景"]}{row["位置"]}{row["违规类别"]}')

    return scenes_result, location_result, violation_category_result


def generate_ngql(scenes_result: List[Document], location_result: List[Document], violation_category_result: List[Document]):

    # INSERT VERTEX `违规类别`(`违法行为描述`, `现场处理措施`) VALUES "关键岗位睡岗":("中央变电所处一人员依靠在电器设备休息。", "严禁人员依靠在电器设备上休息，加强违章人员教育。");

    sgql = "INSERT VERTEX `场景` () VALUES "
    lgql = "INSERT VERTEX `位置` () VALUES "
    vgql = "INSERT VERTEX `违规类别` (`违法行为描述`, `现场处理措施`) VALUES "
    legql = "INSERT EDGE `包括` () VALUES "
    vegql = "INSERT EDGE `涉及` () VALUES "
    for i, s in enumerate(scenes_result):
        if i == len(scenes_result) - 1:
            sgql += f'"{s.page_content}":();'
        else:
            sgql += f'"{s.page_content}":(),'

    for i, l in enumerate(location_result):
        if i == len(location_result) - 1:
            lgql += f'"{l.page_content}":();'
            legql += f'"{l.metadata["source"]}"->"{l.page_content}":();'
        else:
            lgql += f'"{l.page_content}":(),'
            legql += f'"{l.metadata["source"]}"->"{l.page_content}":(),'

    for i, v in enumerate(violation_category_result):
        measure = v.metadata['measure']
        desc = v.metadata['desc']
        if i == len(violation_category_result) - 1:
            vgql += f'"{v.page_content}":("{measure}","{desc}");'
            vegql += f'"{v.metadata["local"]}"->"{v.page_content}":();'
        else:
            vgql += f'"{v.page_content}":("{measure}","{desc}"),'
            vegql += f'"{v.metadata["local"]}"->"{v.page_content}":(),'

    with open("ngql.sql", 'w') as f:
        f.write(sgql+"\n\n\n"+lgql+"\n\n\n"+vgql +
                "\n\n\n" + legql+"\n\n\n" + vegql)


def main():
    scenes_result, location_result, violation_category_result = extra_data(
        file_path=f"app/static/BZ应急素材梳理.xlsx")

    generate_ngql(scenes_result, location_result, violation_category_result)


if __name__ == "__main__":
    main()

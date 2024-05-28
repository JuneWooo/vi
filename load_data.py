# -*- coding:utf-8 -*-

import pandas as pd

from langchain_core.documents import Document

from langchain_community.vectorstores.chroma import Chroma
from app.llms.tali_embedding import TaliAPIEmbeddings
from app.db.chroma import client

embedding_function = TaliAPIEmbeddings()


def init_client():
    try:
        # if client.get_collection("bz_scenes_doc"):
        #     client.delete_collection("bz_scenes_doc")
        # if client.get_collection("bz_location_doc"):
        #     client.delete_collection("bz_location_doc")
        if client.get_collection("bz_knowgele_base_doc"):
            client.delete_collection("bz_knowgele_base_doc")
        if client.get_collection("bz_mapping_doc"):
            client.delete_collection("bz_mapping_doc")

        print("Chroma 数据库清理成功！")
    except Exception as e:
        print(str(e))


def save_bz_doc(file_path):
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
        if f'{row["场景"]}' not in scenes:
            # 场景未写入，插入全部数据
            scenes_result.append(Document(page_content=row["场景"]))
            location_result.append(
                Document(page_content=row["位置"], metadata={"source": row["场景"]}))
            violation_category_result.append(
                Document(page_content=row["违规类别"], metadata={"source": f'{row["场景"]}+{row["位置"]}', "value": row["现场处理措施"]}))
            scenes.append(f'{row["场景"]}')
            location.append(f'{row["场景"]}{row["位置"]}')
            violation_category.append(f'{row["场景"]}{row["位置"]}{row["违规类别"]}')

        elif f'{row["场景"]}{row["位置"]}' not in location:
            # 场景+位置 未写入，插入位置 之后的数据
            location_result.append(
                Document(page_content=row["位置"], metadata={"source": row["场景"]}))
            violation_category_result.append(
                Document(page_content=row["违规类别"], metadata={"source": f'{row["场景"]}+{row["位置"]}', "value": row["现场处理措施"]}))
            location.append(f'{row["场景"]}{row["位置"]}')
            violation_category.append(f'{row["场景"]}{row["位置"]}{row["违规类别"]}')

        elif f'{row["场景"]}{row["位置"]}{row["违规类别"]}' not in violation_category:
            # 场景+位置+违规类别 未写入，插入 违规类别 之后的数据
            violation_category_result.append(
                Document(page_content=row["违规类别"],
                         metadata={"source": f'{row["场景"]}+{row["位置"]}', "value": row["现场处理措施"]}))
            violation_category.append(f'{row["场景"]}{row["位置"]}{row["违规类别"]}')

    Chroma.from_documents(
        documents=scenes_result, collection_name="bz_scenes_doc", embedding=embedding_function, client=client)
    print("scenes docs length", len(scenes_result))
    Chroma.from_documents(documents=location_result,
                          collection_name="bz_location_doc", embedding=embedding_function, client=client)
    print("location docs length", len(location_result))
    Chroma.from_documents(documents=violation_category_result,
                          collection_name="bz_violation_category_doc", embedding=embedding_function, client=client)
    print("violation category docs length", len(violation_category_result))

    print("BZ向量化完成")


def main():
    init_client()
    # file_path = f"app/static/BZ应急素材梳理.xlsx"
    # save_bz_doc(file_path)


if __name__ == "__main__":
    main()

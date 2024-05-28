import json
import asyncio
# from langchain_chroma import Chroma
from langchain_core.prompts.few_shot import FewShotPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
# from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from app import logger
from app.db.chroma import MAPPING_COLLECTION
from app.db.chroma import get_langchain_chroma
# from app.llms.tali_embedding import TaliAPIEmbeddings
from app.schemas.utils_chain import chain, chain_1, rag_chain_with_source


class VideoIdentifyService:

    async def generate_stream_gate(self, scenes, location, violation_category):
        """
        场景、位置、类别生成描述，匹配向量库中的相关案例，进行推理处理决策
            :param scenes: 场景
            :param location: 位置
            :param violation_category: 类别

            :return: 处理措施
        """
        match_content = chain.invoke({
            "scenes": scenes,
            "location": location,
            "violation_category": violation_category
        })

        match_info = get_langchain_chroma(
            MAPPING_COLLECTION).similarity_search(match_content)

        examples = []
        for doc in match_info:
            sce = doc.metadata["scenes"]
            loc = doc.metadata["location"]
            vio = doc.metadata["violation_category"]
            measure = doc.metadata["measure"]
            examples.append({
                "question": f"在{sce}场景，{loc}地点，存在{vio}违规，请给出现场处理措施",
                "answer": f"{measure}"
            })

        question = f"在{scenes}场景，{location}地点，存在{violation_category}违规，请给出现场处理措施"

        example_prompt = PromptTemplate(
            input_variables=["question", "answer"], template="Question: {question}\n{answer}"
        )
        few_shot_prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            suffix="Question: {input}",
            input_variables=["input"],
        )
        few_example = few_shot_prompt.format(input=question)
        logger.warning(f"\n 例子为:{few_example}\n")

        # TODO 根据上传的政策文件的时间 获取最近的上下文，给推理提供背景
        context = []
        source = []
        memory_doc = rag_chain_with_source.invoke(question)
        if memory_doc.get("context"):
            context = memory_doc["context"]
            source = list(set([item.metadata["source"]
                               for item in memory_doc["context"]]))

        logger.warning(f"\n上下文信息:{context}\n来源:{source}\n")

        async for res in chain_1.astream({
            "context": context,
            "example": few_example,
            "scenes": scenes,
            "location": location,
            "violation_category": violation_category,
        }):
            print(res, end="", flush=True)

            yield json.dumps(
                {
                    "scenes": scenes,
                    "location": location,
                    "violation_category": violation_category,
                    "desc": match_content,
                    "message": res,
                    "source": source
                },
                ensure_ascii=False)
            await asyncio.sleep(0.01)


video_identify_service = VideoIdentifyService()

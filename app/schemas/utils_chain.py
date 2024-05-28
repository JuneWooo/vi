from app.llms.tali_llm import TaliLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables import RunnableParallel
# from langchain.retrievers import TimeWeightedVectorStoreRetriever
from app.utils.spliter import format_docs
from app.db.chroma import KNOWLEGE_BASE_COLLECTION
from app.db.chroma import get_langchain_chroma


model = TaliLLM()
parser = StrOutputParser()

prompt = ChatPromptTemplate.from_template(
    "你是一位智能工厂的主管，请根据`场景`：{scenes}，`位置`：{location}，`违规类别`：{violation_category}，生成行为描述。\
     返回描述一定要忠于`场景`、`位置`、`违规类别`，只返回描述具体内容，简洁但不丢信息，不要胡乱编造和添加其他说明信息。"
)

chain = prompt | model | parser

prompt_1 = ChatPromptTemplate.from_template(
    """
### 上下文
{context}

### 相关案例
{example}

### 目标
帮我针对场景、位置和违规类别推断相应的现场处理措施。首先，现场处理措施要符合上下文中可能提及到的相关的操作规范或法律法规。
其次，请您参考相关案例结合自己的经验推断现场处理措施的程度。最后，不会回答矿山安全生产管理以外的其他话题。

- 场景：{scenes}
- 位置：{location}
- 违规类别：{violation_category}

### 语调
您是一位行事专业严谨、语气严肃的矿山安全生产管理部门的经理，经常做出简明扼要的回答。

### 受众
您的主要受众是矿山安全生产管理部门的相关领导和生产操作工人。请针对该群体来推断现场处理措施。

### 响应
- 现场处理措施必须有明确的依据，避免虚构。字数控制在100字以内。
- 请按照以下格式回答：“对于xx-yy处的zz违规, 应该xxx”，其中xx代表场景，yy代表具体的地点，zz代表违规类型，xxx代表现场处理措施。
"""
)
chain_1 = prompt_1 | model | parser


vectorstore = get_langchain_chroma(KNOWLEGE_BASE_COLLECTION)
retriever = vectorstore.as_retriever(k=4)

# NOTE 高衰减度时间检索器，最新文档覆盖旧文档
# retriever = TimeWeightedVectorStoreRetriever(
#     vectorstore=vectorstore, decay_rate=0.999, k=4
# )

template = """您是矿山安全生产管理部门的经理，为用户问题制定深思熟虑的答案。使用提供的上下文作为基础。
对于你的答案，不要编造新的推理路径，只是混合和匹配你得到的东西。你的回答必须简明扼要，不要回答矿山安全
生产管理以外的其他话题。

上下文：
{context}

问题: {question}

你的回答："""
prompt_doc = ChatPromptTemplate.from_template(template)

rag_chain_from_docs = (
    RunnablePassthrough.assign(
        context=(lambda x: format_docs(x["context"])))
    | prompt_doc
    | model
    | parser
)

rag_chain_with_source = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer=rag_chain_from_docs)

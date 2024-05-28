# from fastapi import FastAPI, WebSocket
# from fastapi.responses import StreamingResponse
# import asyncio

# app = FastAPI()

# async def event_generator():
#     for i in range(5):
#         await asyncio.sleep(1)  # 等待一秒
#         yield f"data: Event {i}\n\n"

# @app.get("/events")
# async def get_events():
#     return StreamingResponse(event_generator(), media_type="text/event-stream")

# # 如果你想要一个长时间运行的事件流，可以使用 WebSocket
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     for i in range(5):
#         await asyncio.sleep(1)
#         await websocket.send_json({"event": f"Event {i}"})




from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from app.llms.tali_llm import TaliLLM

model = TaliLLM()

joke_chain = (
    ChatPromptTemplate.from_template("告诉我一个关于 {topic}的笑话")
    | model
)
poem_chain = (
    ChatPromptTemplate.from_template("写一首关于 {topic}的打油诗")
    | model
)

runnable = RunnableParallel(joke=joke_chain, poem=poem_chain)

# Display stream
output = {key: "" for key, _ in runnable.output_schema()}
for chunk in runnable.stream({"topic": "旅行"}):
    for key in chunk:
        output[key] = output[key] + chunk[key].content
    print(output)  # noqa: T201

FROM tiangolo/uvicorn-gunicorn-fastapi:latest

WORKDIR /app
COPY . /app

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


RUN mkdir /static \
    && fc-cache -fv
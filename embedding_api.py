
import torch
from argparse import ArgumentParser
from typing import List
import uvicorn
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):  # collects GPU memory
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


app = FastAPI()


@app.post("/v1/embeddings")
async def emb(texts: List[str]):
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def _get_args():
    parser = ArgumentParser()
    parser.add_argument("--model-path", type=str, default='/root/project/videotest/models/infgrad/stella-large-zh-v3-1792d',
                        help="Model name or path, default to %(default)r")
    parser.add_argument("--server-port", type=int, default=1281,
                        help="Demo server port.")
    parser.add_argument("--server-host", type=str, default="0.0.0.0",
                        help="Demo server name.")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _get_args()
    model = SentenceTransformer(args.model_path, device="cuda")
    uvicorn.run(app, host=args.server_host, port=args.server_port)

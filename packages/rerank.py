import yaml
import numpy as np
from pathlib import Path
from FlagEmbedding import FlagReranker


config_path = Path.cwd() / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
    
MODEL_NAME = config["rerank_model_name"]

reranker_path = Path.cwd() / 'models' / MODEL_NAME
reranker = FlagReranker(reranker_path, use_fp16=True) 

def get_reranker_scores(query: str, contents: str, normalize: bool = True) -> list[np.float64]:
    query_content_pairs = [(query, content) for content in contents]
    scores = reranker.compute_score(query_content_pairs, normalize=normalize)
    return scores


if __name__ == "__main__":
    query = "What is BGE M3?"
    contents = ["Defination of BM25", "What is BGE M3?"]
    scores = get_reranker_scores(query, contents)
    print(scores)

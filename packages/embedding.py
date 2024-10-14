import yaml
from pathlib import Path
from FlagEmbedding import BGEM3FlagModel


config_path = Path.cwd() / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
    
MODEL_NAME = config['embedding_model_name']

embedding_model_path = Path.cwd() / 'models' / MODEL_NAME
embedding_model = BGEM3FlagModel(embedding_model_path,  use_fp16=True) 

def get_embeddings(sentences: list[str]) -> list[list[float]]:
    result = embedding_model.encode(sentences, return_dense=True)
    return result['dense_vecs']


if __name__ == "__main__":
    sentences = ["What is BGE M3?", "Defination of BM25"]
    embeddings = get_embeddings(sentences)

    print(embeddings)
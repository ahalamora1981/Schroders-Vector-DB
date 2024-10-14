import yaml
import chromadb
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from langchain_text_splitters import RecursiveCharacterTextSplitter

from packages.embedding import get_embeddings


config_path = Path.cwd() / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

CHROMA_DB_NAME = config["chroma_db_name"]
CHUNK_SIZE = config["chunk_size"]
CHUNK_OVERLAP = config["chunk_overlap"]

chroma_client_path = str(Path.cwd() / "chroma" / CHROMA_DB_NAME)
chroma_client = chromadb.PersistentClient(path=chroma_client_path)

text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ".", ",", "!", "?", "，", "、", "。", "！", "？", ""],
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    is_separator_regex=False,
)
# text_list = text_splitter.split_text("Some content")

class CollectionResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ok: bool
    message: str
    collection: chromadb.Collection | None = None
    data: dict | None = None


def create_collection(collection_name: str) -> CollectionResponse:
    try:
        collection = chroma_client.create_collection(
            collection_name, 
            metadata={"hnsw:space": "cosine"},
        )
    except chromadb.db.base.UniqueConstraintError:
        return CollectionResponse(
            ok=False,
            message=f"文档集 {collection_name} 已经存在！",
            collection=None
        )
    else:
        return CollectionResponse(
            ok=True,
            message=f"文档集 {collection_name} 创建成功。",
            collection=collection
        )
    
def get_collection(collection_name: str) -> CollectionResponse:
    try:
        collection = chroma_client.get_collection(
            collection_name,
        )
    except chromadb.errors.InvalidCollectionException:
        return CollectionResponse(
            ok=False,
            message=f"文档集 {collection_name} 不存在！",
            collection=None
        )
    else:
        return CollectionResponse(
            ok=True,
            message=f"文档集 {collection_name} 获取成功。",
            collection=collection
        )

def delete_collection(collection_name: str) -> CollectionResponse:
    try:
        chroma_client.delete_collection(collection_name)
    except ValueError:
        return CollectionResponse(
            ok=False,
            message=f"文档集 {collection_name} 不存在！",
        )
    else:
        return CollectionResponse(
            ok=True,
            message=f"文档集 {collection_name} 删除成功。",
        )
        
def add_document_to_collection(
    collection: chromadb.Collection,
    document_name: str,
    document_id: str,
    document: str,
    metadata: dict | None = None,
) -> CollectionResponse:
    texts = text_splitter.split_text(document) 
    embeddings = get_embeddings(texts)
    
    metadata = metadata or {}
    
    metadata['document_name'] = document_name
    metadata['document_id'] = document_id

    metadatas=[metadata for _ in range(len(texts))]
    
    try:
        collection.add(
            ids=[f"{document_name}-{document_id}-#{i}" for i in range(len(texts))],
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts,
        )
    except Exception as e:
        return CollectionResponse(
            ok=False,
            message=f"错误信息: {e}",
        )
    else:
        return CollectionResponse(
            ok=True,
            message=f"文档已添加到文档集 {collection.name} 中。",
            data={"chunks_count": len(texts)}
        )

def get_chunks(
    collection: chromadb.Collection, 
    document_id: str | None = None,
    document_name: str | None = None,
) -> CollectionResponse:
    where = {}

    if document_id:
        where['document_id'] = document_id

    if document_name:
        where['document_name'] = document_name
        
    try:
        response = collection.get(
            where=where,
        )
    except Exception as e:
        return CollectionResponse(
            ok=False,
            message=f"错误信息: {e}",
        )
    else:
        response['chunks_count'] = len(response['ids'])
        return CollectionResponse(
            ok=True,
            message=f"文档片段获取成功。",
            data=response
        )
        
def delete_chunks(
    collection: chromadb.Collection, 
    document_id: str | None = None,
    document_name: str | None = None,
) -> CollectionResponse:
    where = {}

    if document_id:
        where['document_id'] = document_id

    if document_name:
        where['document_name'] = document_name
        
    try:
        collection.delete(
            where=where,
        )
    except Exception as e:
        return CollectionResponse(
            ok=False,
            message=f"错误信息: {e}",
        )
    else:
        return CollectionResponse(
            ok=True,
            message=f"文档片段删除成功。",
        )

if __name__ == "__main__":
    pass
    
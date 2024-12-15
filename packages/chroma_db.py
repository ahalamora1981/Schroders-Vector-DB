import yaml
import chromadb
from chromadb import Settings
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from langchain_text_splitters import RecursiveCharacterTextSplitter

from packages.embedding import get_embeddings
from packages.rerank import get_rerank_scores


config_path = Path.cwd() / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

CHROMA_DB_NAME = config["chroma_db_name"]
CHUNK_SIZE = config["chunk_size"]
CHUNK_OVERLAP = config["chunk_overlap"]
N_RESULTS = config["n_results"]
RERANK_MULTIPLE = config["rerank_multiple"]

chroma_client_path = str(Path.cwd() / "chroma" / CHROMA_DB_NAME)
chroma_client = chromadb.PersistentClient(
    path=chroma_client_path,
    settings=Settings(anonymized_telemetry=False),
)

def sort_list_by_another(list1, list2):
    # 使用 zip 将两个列表组合在一起
    zipped_lists = zip(list1, list2)
    
    # 根据 list1 中的值对组合后的元组进行排序
    sorted_lists = sorted(zipped_lists, key=lambda x: x[0], reverse=True)
    
    # 提取排序后的 list2
    sorted_list2 = [item[1] for item in sorted_lists]
    
    return sorted_list2


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

def list_all_collections() -> CollectionResponse:
    collections = chroma_client.list_collections()

    return CollectionResponse(
        ok=True,
        message=f"文档集列表获取成功。",
        data={"collections": [c.name for c in collections]}
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

def list_all_metadatas_in_collection(collection_name: str) -> CollectionResponse:
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
        metadatas = collection.get(
            include=["metadatas"]
        )['metadatas']

        metadatas_unique = []
        document_ids = []

        for m in metadatas:
            if m['document_id'] not in document_ids:
                document_ids.append(m['document_id'])
                metadatas_unique.append(m)

        return CollectionResponse(
            ok=True,
            message=f"文档集 {collection_name} 所有元数据获取成功。",
            data={"metadatas": metadatas_unique}
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
    document: str,
    metadata: dict,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    separator: str | None = None,
) -> CollectionResponse:
    document_name = metadata['document_name']
    document_id = metadata['document_id']
    
    chunks = get_chunks(collection, document_id)
    
    if chunks.ok:
        if chunks.data['chunks_count'] > 0:
            return CollectionResponse(
                ok=False,
                message=f"文档ID {document_id} 已经存在！",
            )
    else:
        logger.error(chunks.message)

    if chunk_size is None:
        chunk_size=CHUNK_SIZE

    if chunk_overlap is None:
        chunk_overlap=CHUNK_OVERLAP

    if separator is None:
        separators = ["\n\n", "\n", " ", ".", ",", "!", "?", "，", "、", "。", "！", "？", " "]

        text_splitter = RecursiveCharacterTextSplitter(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

        texts = text_splitter.split_text(document)
    else:
        texts = document.split(separator)

    texts = [f"[{document_name}]\n\n{t.strip()}" for t in texts]

    embeddings = get_embeddings(texts)

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
        
def delete_document(
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

def query(
    collection: chromadb.Collection,
    query: str,
    n_results: int = N_RESULTS,
    rerank: bool = False,
    where: dict | None = None,
) -> CollectionResponse:
    if rerank:
        n_results = n_results * RERANK_MULTIPLE
        n_rerank = n_results // RERANK_MULTIPLE

    where = where or {}
    query_embeddings = get_embeddings([query])
    try:
        response = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
        )
    except Exception as e:
        return CollectionResponse(
            ok=False,
            message=f"错误信息: {e}",
        )
    else:
        if rerank:
            rerank_scores = get_rerank_scores(query, response['documents'][0])
            
            response['ids'][0] = sort_list_by_another(rerank_scores, response['ids'][0])[:n_rerank]
            response['documents'][0] = sort_list_by_another(rerank_scores, response['documents'][0])[:n_rerank]
            response['distances'][0] = sort_list_by_another(rerank_scores, response['distances'][0])[:n_rerank]
            response['metadatas'][0] = sort_list_by_another(rerank_scores, response['metadatas'][0])[:n_rerank]
            response['rerank_scores'] = sort_list_by_another(rerank_scores, rerank_scores)[:n_rerank]
            
        return CollectionResponse(
            ok=True,
            message=f"查询成功。",
            data=response
        )


if __name__ == "__main__":
    pass
    
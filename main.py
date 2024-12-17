import yaml
import uvicorn
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from transformers import AutoTokenizer

from packages import chroma_db


config_path = Path.cwd() / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
    
logger_path = Path.cwd() / "logs" / "app.log"
logger_path.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    logger_path, 
    rotation="10 MB", 
    compression="zip"
)

tokenizer_path = Path.cwd() / "models" / "qwen25-72b-tokenizer"
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path) 

app = FastAPI()


class HttpResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ok: bool
    message: str
    data: dict | None = None


class DocumentMetadata(BaseModel):
    category: str = "<|None|>"
    type: str = "<|None|>"
    file_name: str = "<|None|>"
    law_name: str = "<|None|>"
    md5: str = "<|None|>"
    doc_group: str = "<|None|>"
    pub_org_name_list: list[str] | None = None  # 最多10个 


class AddDocumentRequest(BaseModel): 
    model_config = ConfigDict(arbitrary_types_allowed=True)
    collection_name: str
    document_name: str
    document_id: str
    document: str
    metadata: DocumentMetadata
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    separator: str | None = None


class DocumentQueryRequest(BaseModel):
    collection_name: str
    query: str
    n_results: int = 10
    rerank: bool = False
    category: str | None = None
    type: str | None = None
    file_name: str | None = None
    law_name: str | None = None
    md5: str | None = None
    doc_group: str | None = None
    pub_org_name_list: list[str] | None = None


class CountTokensRequest(BaseModel):
    query: str = None


@app.post("/count-tokens")
def count_tokens(query_data: CountTokensRequest):
    query = query_data.query.strip()
    if not query:
        return {
            "ok": False,
            "message": "No query provided",
            "tokens_length": None
        }

    tokens = tokenizer.encode(query, add_special_tokens=True)
    
    return {
        "ok": True,
        "message": "Tokens counted successfully",
        "tokens_length": len(tokens)
    }

@app.get("/create-collection")
def create_collection(collection_name: str) -> HttpResponse:
    response = chroma_db.create_collection(collection_name)
    
    if not response.ok:
        logger.error(response.message)
        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )
        
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data={
            "collection": {
                "name": collection_name,
                "chunks_count": response.collection.count()
            }
        }
    )

@app.get("/list-all-collections")
def list_all_collections() -> HttpResponse:
    response = chroma_db.list_all_collections()

    if not response.ok:
        logger.error(response.message)
        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )
    
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data={
            "collections": response.data['collections']
        }
    )

@app.get("/get-collection")
def get_collection(collection_name: str) -> HttpResponse:
    response = chroma_db.get_collection(collection_name)
    
    if not response.ok:
        logger.error(response.message)
        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )
        
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data={
            "collection": {
                "name": collection_name,
                "chunks_count": response.collection.count()
            }
        },
    )

@app.get("/get-all-metadatas-in-collection")
def get_all_metadatas_in_collection(collection_name: str) -> HttpResponse:
    response = chroma_db.list_all_metadatas_in_collection(collection_name)
    
    if not response.ok:
        logger.error(response.message)
        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )
        
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data=response.data,
    )
    
@app.get("/delete-collection")
def delete_collection(collection_name: str) -> HttpResponse:
    response = chroma_db.delete_collection(collection_name)
    
    if not response.ok:
        logger.error(response.message)
        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )
    
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data=None,
    )
    
@app.post("/add-document")
async def add_document_to_collection(item: AddDocumentRequest) -> HttpResponse:
    metadata = item.metadata.model_dump() 
    
    metadata['document_name'] = item.document_name
    metadata['document_id'] = item.document_id

    # 处理 pub_org_name_list
    for i in range(10):
        if i >= len(metadata['pub_org_name_list']):
            metadata[f'pub_org_name_{i+1}'] = "<|None|>"
        else:
            metadata[f'pub_org_name_{i+1}'] = metadata['pub_org_name_list'][i]

    del metadata['pub_org_name_list']

    print(f"Metadata: {metadata}")

    if not item.document_name:
        return HttpResponse(
            ok=False,
            message="参数 document_name 不能为空。",
            data=None,
        )
    
    if not item.document_id:
        return HttpResponse(
            ok=False,
            message="参数 document_id 不能为空。",
            data=None,
        )
    
    if not item.document:
        return HttpResponse(
            ok=False,
            message="参数 document 不能为空。",
            data=None,
        )
    
    if metadata.get('category') is not None and metadata['category'] not in ['法规', '标准', '内部制度']:
        return HttpResponse(
            ok=False,
            message="参数 category 只能是法规、标准、内部制度中的一个。",
            data=None,
        )
    
    if metadata.get('type') is not None and metadata['type'] not in ['正文', '附件']:
        return HttpResponse(
            ok=False,
            message="参数 type 只能是正文、附件中的一个。",
            data=None,
        )

    collection_name = item.collection_name
    document_name = item.document_name
    document_id = item.document_id
    document = item.document
    chunk_size = item.chunk_size
    chunk_overlap = item.chunk_overlap
    separator = item.separator

    response = chroma_db.get_collection(collection_name)
    
    if not response.ok:
        logger.error(response.message)
        
        return HttpResponse(
            ok=response.ok,
            message=response.message,
            data=None,
        )
    
    collection = response.collection
    
    response = chroma_db.add_document_to_collection(
        collection=collection,
        document=document,
        metadata=metadata,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separator=separator,
    )

    if not response.ok:
        logger.error(response.message)
        
        return HttpResponse(
            ok=response.ok,
            message=response.message,
            data=None,
        )
        
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data={
            "document": {
                "name": document_name,
                "id": document_id,
                "chunks_count": response.data['chunks_count'],
            }
        }
    )

@app.get("/get-chunks")
def get_chunks(
    collection_name: str,
    document_id: str | None = None, 
    document_name: str | None = None,
) -> HttpResponse:
    if (document_id is None and document_name is None):
        logger.error("参数 document_id 和 document_name 至少选一个。")
        return HttpResponse(
            ok=False,
            message="参数 document_id 和 document_name 至少选一个。",
        )
    
    if  (document_id is not None and document_name is not None):
        logger.error("参数 document_id 和 document_name 最多选一个。")
        return HttpResponse(
            ok=False,
            message="参数 document_id 和 document_name 最多选一个。",
        )

    response = chroma_db.get_collection(collection_name)

    if not response.ok:
        logger.error(response.message)

        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )

    collection = response.collection
    response = chroma_db.get_chunks(collection, document_id, document_name)

    if not response.ok:
        logger.error(response.message)

        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )

    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data=response.data,
    )

@app.get("/delete-document")
def delete_document(
    collection_name: str,
    document_id: str | None = None, 
    document_name: str | None = None,
) -> HttpResponse:
    if (document_id is None and document_name is None):
        logger.error("参数 document_id 和 document_name 至少选一个。")
        return HttpResponse(
            ok=False,
            message="参数 document_id 和 document_name 至少选一个。",
        )
    
    if  (document_id is not None and document_name is not None):
        logger.error("参数 document_id 和 document_name 最多选一个。")
        return HttpResponse(
            ok=False,
            message="参数 document_id 和 document_name 最多选一个。",
        )

    response = chroma_db.get_collection(collection_name)

    if not response.ok:
        logger.error(response.message)

        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )

    collection = response.collection
    
    response_get = chroma_db.get_chunks(collection, document_id, document_name)
    
    if not response_get.ok:
        logger.error(response_get.message)

        return HttpResponse(
            ok=response_get.ok,
            message=response_get.message,
        )
    
    print(response_get)
    
    count = response_get.data['chunks_count']

    response_delete = chroma_db.delete_document(collection, document_id, document_name)

    if not response.ok:
        logger.error(response_delete.message)

        return HttpResponse(
            ok=response_delete.ok,
            message=response_delete.message,
        )

    return HttpResponse(
        ok=response_delete.ok,
        message=response_delete.message + f"共删除 {count} 个文档片段。",
        data={"chunks_deleted": count},
    )

@app.post("/query")
def query(item: DocumentQueryRequest) -> HttpResponse:
    response = chroma_db.get_collection(item.collection_name)

    if not response.ok:
        logger.error(response.message)

        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )

    collection = response.collection
    
    if item.n_results > collection.count():
        return HttpResponse(
            ok=False,
            message=f"要获取的文本数量({item.n_results})不能大于文档集文本总数({collection.count()})",
        )

    if item.pub_org_name_list is not None:
        where = {
            "$or": [
                {
                    "pub_org_name_1": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_2": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_3": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_4": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_5": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_6": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_7": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_8": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_9": {
                        "$in": item.pub_org_name_list
                    }
                },
                {
                    "pub_org_name_10": {
                        "$in": item.pub_org_name_list
                    }
                }
            ]
        }
    else:
        where = {
            "$and": []
        }

        if item.category is not None:
            where['$and'].append({
                "category": item.category
            })
            
        if item.type is not None:
            where['$and'].append({
                "type": item.type
            })
            
        if item.file_name is not None:
            where['$and'].append({
                "file_name": item.file_name
            })
            
        if item.law_name is not None:
            where['$and'].append({
                "law_name": item.law_name
            })
            
        if item.md5 is not None:
            where['$and'].append({
                "md5": item.md5
            })
            
        if item.doc_group is not None:
            where['$and'].append({
                "doc_group": item.doc_group
            })

        if len(where['$and']) == 0:
            where = {}
        elif len(where['$and']) == 1:
            where = where['$and'][0]
        else:
            where = where

    response = chroma_db.query(
        collection=collection, 
        query=item.query, 
        n_results=item.n_results,
        rerank=item.rerank,
        where=where,
    )

    if not response.ok:
        logger.error(response.message)
        
        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )
    
    return HttpResponse(
        ok=response.ok,
        message=response.message,
        data=response.data,
    )


if __name__ == "__main__":
    
    uvicorn.run(
        "main:app", 
        host=config['host'], 
        port=config['port'],
        reload=True,
    )

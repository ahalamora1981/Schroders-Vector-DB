import uvicorn
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from packages import chroma_db

logger_path = Path.cwd() / "logs" / "app.log"
logger_path.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    logger_path, 
    rotation="10 MB", 
    compression="zip"
)

app = FastAPI()


class HttpResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    ok: bool
    message: str
    data: dict | None = None


class AddDocumentRequest(BaseModel): 
    model_config = ConfigDict(arbitrary_types_allowed=True)
    collection_name: str
    document_name: str
    document_id: str
    document: str
    metadata: dict | None = None


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
def add_document_to_collection(item: AddDocumentRequest) -> HttpResponse:
    collection_name = item.collection_name
    document_name = item.document_name
    document_id = item.document_id
    document = item.document
    metadata = item.metadata
        
    response = chroma_db.get_collection(collection_name)
    
    if not response.ok:
        logger.error(response.message)
        
        return HttpResponse(
            ok=response.ok,
            message=response.message,
            data=None,
        )
    
    collection = response.collection
    
    if not document_name:
        return HttpResponse(
            ok=False,
            message="参数 document_name 不能为空。",
            data=None,
        )
    
    if not document_id:
        return HttpResponse(
            ok=False,
            message="参数 document_id 不能为空。",
            data=None,
        )
    
    if not document:
        return HttpResponse(
            ok=False,
            message="参数 document 不能为空。",
            data=None,
        )

    if not metadata:
        metadata = {}
    
    response = chroma_db.add_document_to_collection(
        collection=collection,
        document_name=document_name,
        document_id=document_id,
        document=document,
        metadata=metadata,
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

@app.get("/query")
def query(
    collection_name: str,
    query: str,
    n_results: int = 10,
    rerank: bool = False,
) -> HttpResponse:
    response = chroma_db.get_collection(collection_name)

    if not response.ok:
        logger.error(response.message)

        return HttpResponse(
            ok=response.ok,
            message=response.message,
        )

    collection = response.collection

    response = chroma_db.query(
        collection=collection, 
        query=query, 
        n_results=n_results,
        rerank=rerank,
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
        host="localhost", 
        port=8000,
        reload=True,
    )

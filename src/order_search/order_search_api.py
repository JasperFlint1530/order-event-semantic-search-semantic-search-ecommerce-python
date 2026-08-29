import os

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .order_updates import OrderUpdateSearch, SearchRequest, SearchResponse

app = FastAPI(title="Order update semantic search")


@app.post("/search", response_model=SearchResponse)
def search_orders(request: SearchRequest) -> SearchResponse:
    client = InfraiClient()
    search = OrderUpdateSearch(
        client,
        collection=os.getenv("ORDER_COLLECTION", "order-updates"),
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    try:
        return search.search(request)
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": error.code, "detail": error.detail},
        ) from error
    finally:
        client.close()

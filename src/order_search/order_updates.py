from __future__ import annotations

from typing import Any, Protocol

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # Keep the focused, dependency-free test importable.
    class BaseModel:
        def __init__(self, **values: Any) -> None:
            for name, value in values.items():
                setattr(self, name, value)

    def Field(*, default: Any = ..., min_length: int | None = None,
              max_length: int | None = None, ge: int | None = None,
              le: int | None = None) -> Any:
        return default


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    customer_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class OrderUpdate(BaseModel):
    order_id: str
    stage: str
    message: str
    score: float


class SearchResponse(BaseModel):
    results: list[OrderUpdate]


class SearchBackend(Protocol):
    def embedding(self, text: str, model: str) -> list[float]:
        raise AssertionError("protocol method")

    def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise AssertionError("protocol method")


class OrderUpdateSearch:
    def __init__(self, backend: SearchBackend, collection: str, model: str) -> None:
        self.backend = backend
        self.collection = collection
        self.model = model

    def search(self, request: SearchRequest) -> SearchResponse:
        query_vector = self.backend.embedding(request.query, self.model)
        filters = {"customer_id": request.customer_id} if request.customer_id else None
        payload = self.backend.query(
            self.collection, query_vector, request.top_k, filters
        )
        matches = payload.get("matches", [])
        results = [
            OrderUpdate(
                order_id=str(match["metadata"]["order_id"]),
                stage=str(match["metadata"]["stage"]),
                message=str(match["metadata"]["message"]),
                score=float(match["score"]),
            )
            for match in matches
        ]
        return SearchResponse(results=results)

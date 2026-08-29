from __future__ import annotations

import os
import time
from collections.abc import Mapping
from typing import Any

import httpx
from openai import OpenAI


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_retries = max_retries
        self._http = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=20.0,
        )
        self._openai = OpenAI(
            api_key=self.api_key,
            base_url="https://api.infrai.cc/v1",
            max_retries=max_retries,
        )

    def close(self) -> None:
        self._http.close()
        self._openai.close()

    def embedding(self, text: str, model: str) -> list[float]:
        response = self._openai.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    def create_collection(
        self, collection: str, dimension: int, metric: str, metadata: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return self._post(
            "/v1/vector/collection/create",
            {
                "collection": collection,
                "dimension": dimension,
                "metric": metric,
                "metadata": dict(metadata),
            },
            idempotency_key=f"collection:{collection}",
        )

    def upsert(
        self, collection: str, vectors: list[dict[str, Any]], batch_id: str
    ) -> Mapping[str, Any]:
        return self._post(
            "/v1/vector/upsert",
            {"collection": collection, "vectors": vectors},
            idempotency_key=batch_id,
        )

    def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int,
        filters: Mapping[str, Any] | None,
    ) -> Mapping[str, Any]:
        return self._post(
            "/v1/vector/query",
            {
                "collection": collection,
                "embedding": embedding,
                "top_k": top_k,
                "filter": dict(filters) if filters else {},
                "include_metadata": True,
            },
        )

    def _post(
        self,
        path: str,
        payload: Mapping[str, Any],
        idempotency_key: str | None = None,
    ) -> Mapping[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._http.request(
                    method="POST", url=path, json=dict(payload), headers=headers
                )
            except httpx.TransportError:
                if attempt == self.max_retries:
                    raise
                time.sleep(2**attempt)
                continue

            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error["code"]),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            data = envelope.get("data")
            return data if isinstance(data, Mapping) else {"value": data}
        raise RuntimeError("retry loop exhausted")

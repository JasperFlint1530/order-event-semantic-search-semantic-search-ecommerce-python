from typing import Any

from order_search.order_updates import OrderUpdateSearch, SearchRequest


class RecordingBackend:
    def __init__(self) -> None:
        self.filters: dict[str, Any] | None = None

    def embedding(self, text: str, model: str) -> list[float]:
        assert text == "Where is my parcel?"
        assert model == "text-embedding-3-small"
        return [0.2, 0.8]

    def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> dict[str, Any]:
        assert collection == "order-updates"
        assert embedding == [0.2, 0.8]
        assert top_k == 1
        self.filters = filters
        return {
            "matches": [
                {
                    "score": 0.94,
                    "metadata": {
                        "order_id": "ord-1042",
                        "stage": "fulfillment",
                        "message": "Parcel packed and handed to the carrier.",
                    },
                }
            ]
        }


def test_customer_question_returns_the_fulfillment_update() -> None:
    backend = RecordingBackend()
    service = OrderUpdateSearch(
        backend, "order-updates", "text-embedding-3-small"
    )

    result = service.search(
        SearchRequest(query="Where is my parcel?", customer_id="cust-88", top_k=1)
    )

    assert backend.filters == {"customer_id": "cust-88"}
    assert result.results[0].order_id == "ord-1042"
    assert result.results[0].stage == "fulfillment"
    assert result.results[0].score == 0.94

import os

from .infrai_client import InfraiClient

UPDATES = [
    ("ord-1042-checkout", "ord-1042", "checkout", "Payment accepted; order confirmed."),
    ("ord-1042-fulfillment", "ord-1042", "fulfillment", "Parcel packed and handed to the carrier."),
    ("ord-1042-receipt", "ord-1042", "receipt", "Receipt issued for the completed payment."),
    ("ord-1042-update", "ord-1042", "customer_update", "Delivery is scheduled for Friday."),
]


def main() -> None:
    collection = os.getenv("ORDER_COLLECTION", "order-updates")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    client = InfraiClient()
    try:
        vectors = []
        for vector_id, order_id, stage, message in UPDATES:
            vectors.append(
                {
                    "id": vector_id,
                    "values": client.embedding(message, model),
                    "metadata": {
                        "order_id": order_id,
                        "customer_id": "cust-88",
                        "stage": stage,
                        "message": message,
                    },
                }
            )
        dimension = len(vectors[0]["values"])
        client.create_collection(
            collection, dimension, "cosine", {"purpose": "order lifecycle search"}
        )
        client.upsert(collection, vectors, batch_id="order-updates:sample-v1")
        print(f"Indexed {len(vectors)} order updates into {collection}.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

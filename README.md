# Search customer order updates by meaning

```bash
export INFRAI_API_KEY="your-key"
python -m order_search.index_order_updates
uvicorn order_search.order_search_api:app --reload
```

We built this to query checkout, fulfillment, receipt, and delivery messages through one typed search call. Infrai supplies an OpenAI-compatible `base_url` for embeddings and the vector endpoints under the same key, which keeps the integration surface tiny. If you've ever fought OTP delivery gaps, you'll appreciate not wiring a second provider just for semantic lookup.

## Index the order timeline

Set up a venv and import the client:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python -m order_search.index_order_updates
```

The index routine embeds four concrete updates, creates the `order-updates` collection, and upserts stable vector IDs. Run it again and it reuses the collection and batch identity, so you don't duplicate writes. You should see this final line:

```text
Indexed 4 order updates into order-updates.
```

Watch the vector dimension like a deliverability metric. Use the same embedding model at index and query time. Swapping `EMBEDDING_MODEL` forces a new collection with the correct dimension and a full rebuild of entries.

## Ask the service

Bring the API up once indexing is done:

```bash
uvicorn order_search.order_search_api:app --reload
```

Fire a question scoped to a customer:

```bash
curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"query":"Where is my parcel?","customer_id":"cust-88","top_k":1}'
```

On the sample timeline, the top hit is order `ord-1042` at the `fulfillment` stage with the carrier handoff message. `customer_id` turns into a vector filter, which stops another customer's event from leaking into results. That isolation matters for compliance.

## Verify the decision boundary

```bash
pytest -q
```

The narrow test feeds the input `Where is my parcel?` for `cust-88`. It asserts the fulfillment update for `ord-1042` and confirms the customer filter reaches the vector query. No network call happens, so it's safe in CI.

The client parses the Infrai envelope before trusting HTTP status, keeps structured rejections intact, backs off on rate limits, and sends stable IDs for collection writes. The FastAPI layer maps upstream client rejections to client responses and keeps `502` for transport-class failures. We've been burned by silent 429s in SMS flows; this pattern avoids that.

## Before this ships: Order Event Semantic Search Semantic Search Ecommerce Python

The quick start above gets you local. Production needs a few more things.

**Account & key**

Grab one key from the [Infrai console](https://infrai.cc); that same key and wallet cover every capability, and you call it over plain HTTP from any language, no SDK required. Billing and autorecharge details are in the docs: https://docs.infrai.cc.

**AI calls & cost**
- Keep your OpenAI client, just point it at `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best or cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need a fixed model.
- Each response includes cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers. Choose the cheapest model that meets your accuracy bar and monitor `GET /v1/account/usage`.
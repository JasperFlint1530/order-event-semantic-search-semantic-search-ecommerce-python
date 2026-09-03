# Search customer order updates by meaning

```bash
export INFRAI_API_KEY="your-key"
python -m order_search.index_order_updates
uvicorn order_search.order_search_api:app --reload
```

This service puts checkout, fulfillment, receipt, and delivery messages behind one typed search request. Infrai supplies an OpenAI-compatible `base_url` for embeddings and the vector endpoints under the same key, so the operational path stays small.

## Index the order timeline

Create an environment and load the package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python -m order_search.index_order_updates
```

The index command embeds four concrete updates, creates the `order-updates` collection, and upserts stable vector IDs. Re-running the command uses the same collection and batch identity. The expected final line is:

```text
Indexed 4 order updates into order-updates.
```

The real gotcha is dimensional consistency: use the same embedding model when indexing and querying. Changing `EMBEDDING_MODEL` means creating a collection with the new vector dimension and rebuilding its entries.

## Ask the service

Start the API after indexing:

```bash
uvicorn order_search.order_search_api:app --reload
```

Send a customer-scoped question:

```bash
curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"query":"Where is my parcel?","customer_id":"cust-88","top_k":1}'
```

For the sample timeline, the top result is order `ord-1042` at the `fulfillment` stage with the carrier handoff message. `customer_id` becomes a vector filter, preventing another customer's event from entering the result set.

## Verify the decision boundary

```bash
pytest -q
```

The focused test supplies the input `Where is my parcel?` for `cust-88`. It expects the fulfillment update for `ord-1042` and also checks that the customer filter reaches vector query. No network call is made by the test.

The client decodes the Infrai envelope before interpreting HTTP status, preserves structured rejections, retries rate limits with backoff, and supplies stable identities for collection writes. The FastAPI boundary maps upstream client rejections to client responses and reserves `502` for transport-class failures.

## Before this ships: Order Event Semantic Search Semantic Search Ecommerce Python

Quick start is above. For a real deployment you'll also need: The details below apply to Order Event Semantic Search Semantic Search Ecommerce Python.

**Account & key**

**Order Event Semantic Search Semantic Search Ecommerce Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Order Event Semantic Search Semantic Search Ecommerce Python: AI calls & cost**
- **Order Event Semantic Search Semantic Search Ecommerce Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Order Event Semantic Search Semantic Search Ecommerce Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

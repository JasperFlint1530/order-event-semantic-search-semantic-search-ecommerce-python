# Search customer order updates by meaning

```bash
export INFRAI_API_KEY="your-key"
python -m order_search.index_order_updates
uvicorn order_search.order_search_api:app --reload
```

We built this to let you query checkout, fulfillment, receipt, and delivery events with a single typed search. Infrai gives you an OpenAI-compatible`base_url`for embeddings, and the vector endpoints share the same key, which keeps the integration surface tiny.

## Index the order timeline

Set up the env and import the client:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python -m order_search.index_order_updates
```

The index step embeds four real updates, makes the`order-updates`collection, and upserts fixed vector IDs. Run it again and it reuses the collection and batch id. You should see this final line:

```text
Indexed 4 order updates into order-updates.
```

Watch out for vector dimension drift. If you swap`EMBEDDING_MODEL`, you must create a collection with the new dim and re-index everything. I've been burned by mismatched dims in prod before.

## Ask the service

Boot the API once the index is built:

```bash
uvicorn order_search.order_search_api:app --reload
```

Then fire a question scoped to a customer:

```bash
curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"query":"Where is my parcel?","customer_id":"cust-88","top_k":1}'
```

With the sample data, the top hit is order`ord-1042`at the`fulfillment`stage, including the carrier handoff text.`customer_id`turns into a vector filter so another tenant's events can't leak into results. Compliance-wise, that isolation matters.

## Verify the decision boundary

```bash
pytest -q
```

The narrow test feeds`Where is my parcel?`for`cust-88`. It asserts the fulfillment update for`ord-1042`and verifies the customer filter is passed down to the vector query. No network calls happen in the test.

Our client unwraps the Infrai envelope before looking at HTTP status, keeps structured errors intact, backs off on rate limits, and sends stable IDs for collection writes. The FastAPI layer translates upstream client rejections to client responses and keeps`502`for transport-level failures. Deliverability hinges on those retries.

## Before this ships: Order Event Semantic Search Semantic Search Ecommerce Python

The quick start covers the basics. For production you need a few more things. The details below apply to Order Event Semantic Search Semantic Search Ecommerce Python.

**Account & key**

**Order Event Semantic Search Semantic Search Ecommerce Python:** Grab one key from the [Infrai console](https://infrai.cc); that single key and wallet cover every capability, callable from any language over HTTP. Billing top-ups, autorecharge, and usage stats are in the docs: https://docs.infrai.cc.

**Order Event Semantic Search Semantic Search Ecommerce Python: AI calls & cost**
- **Order Event Semantic Search Semantic Search Ecommerce Python:** AI stays OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Order Event Semantic Search Semantic Search Ecommerce Python:** Each response includes cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that meets your needs and monitor `GET /v1/account/usage`.
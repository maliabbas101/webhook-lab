# Webhook Lab

A local playground for understanding webhook retries and duplicate processing. Configure a receiver response sequence, deliver several copies of one event, and export every simulated attempt as JSON.

## Run

Python 3.11 or newer. No third-party packages or credentials required.

```sh
python lab.py
```

Open http://127.0.0.1:8000. The server binds to localhost; this is a local demo, not a production webhook receiver.

```sh
python -m unittest -v
```

## Try it

1. Run `500,500,200` to see recovery after exponential backoff.
2. Run the Duplicates preset with deduplication enabled: two successful deliveries produce one side effect.
3. Disable deduplication and rerun: the same deliveries produce two side effects.
4. Run `503` to exhaust the retry budget. Export the log for comparison.

## Model

Each copy starts the configured status sequence from the beginning. When the sequence ends, its final status repeats. Any 2xx response is acknowledged; 408, 429 and 5xx responses retry up to the attempt budget. Other statuses stop the copy. Retry delays are `initial_delay * 2 ** (attempt - 1)` and advance virtual time without sleeping.

Copies execute sequentially and share a single event identity. Deduplication records successful processing for the duration of one simulation. This makes the difference between acknowledgements and side effects visible. It does not model concurrent duplicate races or guarantee exactly-once processing in a real system.

`POST /api/simulate` accepts `statuses`, `copies`, `attempts`, `delay`, and `deduplicate`. `GET /health` provides a health check.

## Limits and next steps

This version simulates delivery rather than sending network traffic. State is not persisted. It does not implement signatures, jitter, Retry-After, provider-specific policies, or real endpoint replay. A real receiver would need durable idempotency storage and atomic handling of business side effects. No employer code or patient data is included.

No hosted demo is deployed yet. Run locally using the commands above.

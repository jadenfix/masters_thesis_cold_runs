# Crypto data collection research

The notebook collects Coinbase prices, news and Twitter data. Price collection now normalizes symbols, rejects invalid windows/granularities, advances bounded request windows even when a provider repeats stale candles, and deduplicates UTC rows.

```sh
python -m pip install -r requirements-smoke.txt
python -m unittest discover -s tests -v
```

The three tests execute the notebook's actual price functions without loading unrelated news/Twitter dependencies. A separate live smoke collected 24 BTC-USD hourly candles from Coinbase and exported the standardized CSV. This verifies that price lane only: news ingestion, Twitter login, optional API credentials and long-history completeness remain separate unverified integrations.

Cached notebook outputs were cleared after changing the data boundary; rerun explicitly rather than treating prior displayed outputs as validation of the revised workflow.

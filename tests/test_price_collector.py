"""Execute the notebook's price functions without news/Twitter credentials."""
import ast
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]


def notebook_functions():
    notebook = json.loads((ROOT / "combined_data_fetcher_py.ipynb").read_text())
    source = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    source = "\n".join(line for line in source.splitlines()
                       if not line.startswith(("!", "%")))
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {"standardize_timestamp", "fetch_historical_prices"}]
    scope = {"pd": pd, "requests": SimpleNamespace(get=Mock(), exceptions=requests.exceptions),
             "datetime": datetime, "timedelta": timedelta, "timezone": timezone,
             "time": SimpleNamespace(sleep=lambda _: None), "traceback": SimpleNamespace(print_exc=lambda: None),
             "COINBASE_API_URL": "https://api.exchange.coinbase.com"}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(ROOT), "exec"), scope)
    return scope


class CollectorTests(unittest.TestCase):
    def test_stale_provider_data_cannot_loop(self):
        scope = notebook_functions()
        response = Mock()
        response.json.return_value = [[1577836800, 1, 2, 1.2, 1.4, 3]]
        scope["requests"].get.return_value = response
        frame = scope["fetch_historical_prices"]("btc-usd", days_history=1, granularity=86400)
        self.assertEqual(scope["requests"].get.call_count, 1)
        self.assertEqual(scope["requests"].get.call_args.args[0],
                         "https://api.exchange.coinbase.com/products/BTC-USD/candles")
        self.assertTrue(frame.empty)

    def test_valid_candles_roundtrip_csv(self):
        scope = notebook_functions()
        stamp = int((datetime.now(timezone.utc) - timedelta(hours=12)).timestamp())
        response = Mock()
        response.json.return_value = [[stamp, 1, 2, 1.2, 1.4, 3], [stamp, 1, 2, 1.2, 1.4, 3]]
        scope["requests"].get.return_value = response
        frame = scope["fetch_historical_prices"]("BTC", days_history=1, granularity=86400)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["coin"], "BTC")
        self.assertEqual(str(frame["timestamp"].dt.tz), "UTC")
        self.assertIn("timestamp,coin,source,low,high,open,close,volume", frame.to_csv(index=False))

    def test_invalid_collection_parameters(self):
        function = notebook_functions()["fetch_historical_prices"]
        for args in ({"days_history": 0}, {"granularity": 1}):
            with self.assertRaises(ValueError):
                function("BTC", **args)

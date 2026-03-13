import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

logger = setup_logger("client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error [{code}]: {message}")


class BinanceClient:
    """
    Lightweight wrapper around the Binance Futures Testnet REST API.
    Handles authentication, request signing, and error parsing.
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceClient initialized (testnet)")

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 signature for the given params dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse response; raise BinanceAPIError on non-2xx or error body."""
        logger.debug(f"HTTP {response.status_code} | URL: {response.url}")
        try:
            data = response.json()
        except Exception:
            response.raise_for_status()
            return {}

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            logger.error(f"API error response: {data}")
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        if not response.ok:
            logger.error(f"HTTP error {response.status_code}: {data}")
            response.raise_for_status()

        logger.debug(f"API response: {data}")
        return data

    # ------------------------------------------------------------------ #
    #  Public API methods                                                  #
    # ------------------------------------------------------------------ #

    def get_server_time(self) -> Dict[str, Any]:
        """Ping the server and return server time (no auth required)."""
        url = f"{BASE_URL}/fapi/v1/time"
        logger.debug(f"GET {url}")
        response = self.session.get(url, timeout=10)
        return self._handle_response(response)

    def get_exchange_info(self) -> Dict[str, Any]:
        """Return exchange trading rules and symbol info."""
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        logger.debug(f"GET {url}")
        response = self.session.get(url, timeout=10)
        return self._handle_response(response)

    def get_account_info(self) -> Dict[str, Any]:
        """Return account balance and position info (signed)."""
        url = f"{BASE_URL}/fapi/v2/account"
        params: Dict[str, Any] = {"timestamp": self._timestamp()}
        params["signature"] = self._sign(params)
        logger.debug(f"GET {url} | params: {params}")
        response = self.session.get(url, params=params, timeout=10)
        return self._handle_response(response)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place a new futures order on the testnet.

        Parameters
        ----------
        symbol        : e.g. "BTCUSDT"
        side          : "BUY" or "SELL"
        order_type    : "MARKET", "LIMIT", or "STOP_MARKET"
        quantity      : order quantity
        price         : required for LIMIT orders
        time_in_force : "GTC" | "IOC" | "FOK"  (ignored for MARKET)
        stop_price    : required for STOP_MARKET orders
        """
        url = f"{BASE_URL}/fapi/v1/order"

        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": self._timestamp(),
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("stopPrice is required for STOP_MARKET orders.")
            params["stopPrice"] = stop_price

        params["signature"] = self._sign(params)

        logger.info(
            f"Placing order → symbol={symbol} side={side} type={order_type} "
            f"qty={quantity} price={price} stopPrice={stop_price}"
        )
        logger.debug(f"POST {url} | params: {params}")

        response = self.session.post(url, data=params, timeout=10)
        result = self._handle_response(response)
        logger.info(f"Order placed successfully | orderId={result.get('orderId')}")
        return result

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order by orderId."""
        url = f"{BASE_URL}/fapi/v1/order"
        params: Dict[str, Any] = {
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": self._timestamp(),
        }
        params["signature"] = self._sign(params)
        logger.info(f"Cancelling order | symbol={symbol} orderId={order_id}")
        response = self.session.delete(url, params=params, timeout=10)
        return self._handle_response(response)

    def get_open_orders(self, symbol: Optional[str] = None) -> Any:
        """Return all open orders, optionally filtered by symbol."""
        url = f"{BASE_URL}/fapi/v1/openOrders"
        params: Dict[str, Any] = {"timestamp": self._timestamp()}
        if symbol:
            params["symbol"] = symbol
        params["signature"] = self._sign(params)
        logger.debug(f"GET {url} | params: {params}")
        response = self.session.get(url, params=params, timeout=10)
        return self._handle_response(response)

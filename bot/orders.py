from typing import Optional

import requests

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger
from bot.validators import validate_all, ValidationError

logger = setup_logger("orders")


def _print_separator(char: str = "─", width: int = 60) -> None:
    print(char * width)


def _print_order_summary(params: dict) -> None:
    """Print a formatted summary of the order request."""
    _print_separator()
    print("📋  ORDER REQUEST SUMMARY")
    _print_separator()
    print(f"  Symbol     : {params['symbol']}")
    print(f"  Side       : {params['side']}")
    print(f"  Type       : {params['order_type']}")
    print(f"  Quantity   : {params['quantity']}")
    if params.get("price"):
        print(f"  Price      : {params['price']}")
    _print_separator()


def _print_order_response(response: dict) -> None:
    """Print a formatted summary of the order response."""
    print("✅  ORDER RESPONSE")
    _print_separator()
    print(f"  Order ID      : {response.get('orderId', 'N/A')}")
    print(f"  Client OID    : {response.get('clientOrderId', 'N/A')}")
    print(f"  Symbol        : {response.get('symbol', 'N/A')}")
    print(f"  Side          : {response.get('side', 'N/A')}")
    print(f"  Type          : {response.get('type', 'N/A')}")
    print(f"  Status        : {response.get('status', 'N/A')}")
    print(f"  Orig Qty      : {response.get('origQty', 'N/A')}")
    print(f"  Executed Qty  : {response.get('executedQty', 'N/A')}")
    avg_price = response.get("avgPrice") or response.get("price", "N/A")
    print(f"  Avg Price     : {avg_price}")
    print(f"  Time in Force : {response.get('timeInForce', 'N/A')}")
    print(f"  Update Time   : {response.get('updateTime', 'N/A')}")
    _print_separator()


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    time_in_force: str = "GTC",
) -> None:
    """
    Validate inputs, place the order, and print results.
    Handles all exceptions and logs everything.
    """
    # ── Validation ────────────────────────────────────────────────────── #
    try:
        params = validate_all(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        print(f"\n❌  VALIDATION ERROR: {e}\n")
        return

    _print_order_summary(params)

    # ── Place Order ───────────────────────────────────────────────────── #
    # For STOP_MARKET the validated price goes into stop_price, not price
    is_stop = params["order_type"] == "STOP_MARKET"
    try:
        response = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=None if is_stop else params["price"],
            stop_price=params["price"] if is_stop else None,
            time_in_force=time_in_force,
        )
        _print_order_response(response)
        print(f"🎉  Order placed successfully! Order ID: {response.get('orderId')}\n")
        logger.info(f"Order success | response={response}")

    except BinanceAPIError as e:
        logger.error(f"Binance API error: {e}")
        print(f"\n❌  API ERROR [{e.code}]: {e.message}\n")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Network connection error: {e}")
        print(f"\n❌  NETWORK ERROR: Could not connect to Binance. Check your internet connection.\n")

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out: {e}")
        print(f"\n❌  TIMEOUT: The request timed out. Please try again.\n")

    except Exception as e:
        logger.exception(f"Unexpected error while placing order: {e}")
        print(f"\n❌  UNEXPECTED ERROR: {e}\n")

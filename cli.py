#!/usr/bin/env python3
"""
Trading Bot CLI — Binance Futures Testnet
=========================================
Usage examples:

  # Market BUY
  python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit SELL
  python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

  # Stop-Market BUY
  python cli.py order --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --price 95000

  # Account info
  python cli.py account

  # List open orders
  python cli.py open-orders --symbol BTCUSDT
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import place_order

load_dotenv()
logger = setup_logger("cli")

BANNER = """
╔══════════════════════════════════════════════════════╗
║         🤖  Binance Futures Testnet Trading Bot       ║
╚══════════════════════════════════════════════════════╝
"""


def get_client() -> BinanceClient:
    """Load API credentials from environment and return a BinanceClient."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print("❌  ERROR: BINANCE_API_KEY and BINANCE_API_SECRET must be set.")
        print("   Create a .env file or export them as environment variables.")
        print("   See README.md for setup instructions.")
        sys.exit(1)

    return BinanceClient(api_key, api_secret)


# ── Sub-command handlers ─────────────────────────────────────────────────── #

def cmd_order(args: argparse.Namespace) -> None:
    """Handle the 'order' sub-command."""
    client = get_client()
    place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=str(args.quantity),
        price=str(args.price) if args.price is not None else None,
        time_in_force=args.tif,
    )


def cmd_account(args: argparse.Namespace) -> None:
    """Handle the 'account' sub-command."""
    client = get_client()
    try:
        info = client.get_account_info()
        print("\n📊  ACCOUNT INFO")
        print("─" * 60)
        print(f"  Total Wallet Balance   : {info.get('totalWalletBalance')} USDT")
        print(f"  Unrealized PnL         : {info.get('totalUnrealizedProfit')} USDT")
        print(f"  Available Balance      : {info.get('availableBalance')} USDT")
        print(f"  Total Margin Balance   : {info.get('totalMarginBalance')} USDT")
        print("─" * 60)

        assets = [a for a in info.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
        if assets:
            print("\n  Non-zero Asset Balances:")
            for asset in assets:
                print(f"    {asset['asset']}: {asset['walletBalance']}")
        print()
        logger.info("Account info fetched successfully.")
    except Exception as e:
        logger.error(f"Failed to fetch account info: {e}")
        print(f"\n❌  ERROR: {e}\n")


def cmd_open_orders(args: argparse.Namespace) -> None:
    """Handle the 'open-orders' sub-command."""
    client = get_client()
    try:
        orders = client.get_open_orders(symbol=args.symbol)
        print("\n📂  OPEN ORDERS")
        print("─" * 60)
        if not orders:
            print("  No open orders found.")
        else:
            for o in orders:
                print(
                    f"  [{o.get('orderId')}] {o.get('symbol')} | {o.get('side')} "
                    f"{o.get('type')} | qty={o.get('origQty')} | price={o.get('price')} "
                    f"| status={o.get('status')}"
                )
        print("─" * 60)
        print()
        logger.info(f"Fetched {len(orders)} open orders.")
    except Exception as e:
        logger.error(f"Failed to fetch open orders: {e}")
        print(f"\n❌  ERROR: {e}\n")


def cmd_cancel(args: argparse.Namespace) -> None:
    """Handle the 'cancel' sub-command."""
    client = get_client()
    try:
        result = client.cancel_order(symbol=args.symbol.upper(), order_id=args.order_id)
        print(f"\n✅  Order {result.get('orderId')} cancelled successfully.\n")
        logger.info(f"Order cancelled | orderId={result.get('orderId')}")
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        print(f"\n❌  ERROR: {e}\n")


# ── Argument Parser ──────────────────────────────────────────────────────── #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    # ── order ── #
    order_parser = subparsers.add_parser("order", help="Place a new order")
    order_parser.add_argument(
        "--symbol", required=True, type=str,
        help="Trading pair symbol, e.g. BTCUSDT"
    )
    order_parser.add_argument(
        "--side", required=True, type=str, choices=["BUY", "SELL"],
        help="Order side: BUY or SELL"
    )
    order_parser.add_argument(
        "--type", required=True, type=str,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        dest="type",
        help="Order type: MARKET, LIMIT, or STOP_MARKET (bonus)"
    )
    order_parser.add_argument(
        "--quantity", required=True, type=float,
        help="Order quantity (e.g. 0.001 for BTC)"
    )
    order_parser.add_argument(
        "--price", required=False, type=float, default=None,
        help="Limit/stop price (required for LIMIT and STOP_MARKET)"
    )
    order_parser.add_argument(
        "--tif", required=False, type=str, default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC)"
    )
    order_parser.set_defaults(func=cmd_order)

    # ── account ── #
    account_parser = subparsers.add_parser("account", help="Show account balance info")
    account_parser.set_defaults(func=cmd_account)

    # ── open-orders ── #
    oo_parser = subparsers.add_parser("open-orders", help="List open orders")
    oo_parser.add_argument(
        "--symbol", required=False, type=str, default=None,
        help="Filter by symbol (optional)"
    )
    oo_parser.set_defaults(func=cmd_open_orders)

    # ── cancel ── #
    cancel_parser = subparsers.add_parser("cancel", help="Cancel an open order")
    cancel_parser.add_argument("--symbol", required=True, type=str)
    cancel_parser.add_argument("--order-id", required=True, type=int, dest="order_id")
    cancel_parser.set_defaults(func=cmd_cancel)

    return parser


def main() -> None:
    print(BANNER)
    parser = build_parser()
    args = parser.parse_args()
    logger.info(f"CLI command: {args.command} | args: {vars(args)}")
    args.func(args)


if __name__ == "__main__":
    main()

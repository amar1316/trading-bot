from typing import Optional
from bot.logging_config import setup_logger

logger = setup_logger("validators")

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}
VALID_TIF = {"GTC", "IOC", "FOK"}


class ValidationError(Exception):
    """Raised when user input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    """Validate and normalize trading symbol."""
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string.")
    symbol = symbol.strip().upper()
    if len(symbol) < 3:
        raise ValidationError(f"Symbol '{symbol}' is too short. Example: BTCUSDT")
    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY or SELL)."""
    if not side:
        raise ValidationError("Side must be specified.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        )
    logger.debug(f"Side validated: {side}")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type."""
    if not order_type:
        raise ValidationError("Order type must be specified.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )
    logger.debug(f"Order type validated: {order_type}")
    return order_type


def validate_quantity(quantity: str) -> float:
    """Validate order quantity."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a valid number. Got: '{quantity}'")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0. Got: {qty}")
    logger.debug(f"Quantity validated: {qty}")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """Validate price — required for LIMIT and STOP_MARKET orders."""
    if order_type == "MARKET":
        if price is not None:
            logger.debug("Price provided for MARKET order — will be ignored.")
        return None

    if order_type in ("LIMIT", "STOP_MARKET"):
        if price is None:
            raise ValidationError(f"Price is required for {order_type} orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a valid number. Got: '{price}'")
        if p <= 0:
            raise ValidationError(f"Price must be greater than 0. Got: {p}")
        logger.debug(f"Price validated: {p}")
        return p

    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
) -> dict:
    """
    Run all validations and return a clean, validated parameter dict.
    Raises ValidationError on first failure.
    """
    logger.debug("Starting input validation...")
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper() if order_type else ""),
    }
    logger.debug(f"All inputs validated: {validated}")
    return validated

"""Authorized e-commerce data connectors."""

from app.connectors.amazon import AmazonConnector
from app.connectors.base import (
    BaseConnector,
    ConnectorError,
    ConnectorResult,
    NormalizedOffer,
    run_connectors,
)
from app.connectors.mercadolivre import MercadoLivreConnector
from app.connectors.shopee import ShopeeConnector

__all__ = [
    "AmazonConnector",
    "BaseConnector",
    "ConnectorError",
    "ConnectorResult",
    "MercadoLivreConnector",
    "NormalizedOffer",
    "ShopeeConnector",
    "run_connectors",
]

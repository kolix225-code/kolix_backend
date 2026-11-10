# app/models/__init__.py
from app.core.database import Base
from app.models.base import UUIDModel, TimestampMixin, SoftDeleteMixin
from app.models.user import User, Collaborator
from app.models.shop import Shop, StoreCustomization, StoreTemplate
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.inventory import InventoryItem, StockMovement
from app.models.wallet import Wallet, PayoutAccount, WalletTransaction
from app.models.accounting import Charge
from app.models.client import Client
from app.models.whatsapp import WhatsAppCampaign, WhatsAppMessage, SavedAudience
from app.models.affiliate import Affiliate, AffiliateReferral, AffiliatePayout
from app.models.settings import StoreSettings
from app.models.ai import AiConversation, AiMessage

__all__ = [
    "Base",
    "UUIDModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "Collaborator",
    "Shop",
    "StoreCustomization",
    "StoreTemplate",
    "Product",
    "Order",
    "OrderItem",
    "InventoryItem",
    "StockMovement",
    "Wallet",
    "PayoutAccount",
    "WalletTransaction",
    "Charge",
    "Client",
    "WhatsAppCampaign",
    "WhatsAppMessage",
    "SavedAudience",
    "Affiliate",
    "AffiliateReferral",
    "AffiliatePayout",
    "StoreSettings",
    "AiConversation",
    "AiMessage",
]


# app/schemas/__init__.py
from app.schemas.common import BaseSchema, StandardResponse, PaginatedResponse
from app.schemas.auth import (
    RegisterStep1Request,
    RegisterStep1Response,
    VerifyOtpRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    VerifyResetOtpRequest,
    ResetPasswordRequest,
)
from app.schemas.user import CollaboratorCreate, CollaboratorUpdate, CollaboratorResponse
from app.schemas.shop import (
    ShopCreate,
    ShopResponse,
    StoreTemplateResponse,
    StoreCustomizationUpdate,
    StoreCustomizationResponse,
)
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, BulkStatusRequest
from app.schemas.order import (
    OrderItemSchema,
    PublicCheckoutRequest,
    OrderUpdateStatusRequest,
    OrderAssignDeliveryRequest,
    OrderResponse,
)
from app.schemas.inventory import (
    RestockRequest,
    ThresholdUpdateRequest,
    InventoryItemResponse,
    StockKpisResponse,
)
from app.schemas.wallet import (
    WalletSummaryResponse,
    PayoutAccountCreate,
    PayoutAccountResponse,
    WithdrawRequest,
    WalletTransactionResponse,
)
from app.schemas.accounting import ChargeCreate, ChargeResponse, AccountingDashboardResponse
from app.schemas.client import ClientResponse
from app.schemas.whatsapp import (
    WhatsAppCampaignCreate,
    WhatsAppCampaignResponse,
    SavedAudienceCreate,
    SavedAudienceResponse,
)
from app.schemas.affiliate import (
    AffiliateReferralResponse,
    AffiliateSummaryResponse,
    TransferCommissionRequest,
)
from app.schemas.settings import (
    StoreSettingsGeneralUpdate,
    StoreSettingsCodFormUpdate,
    StoreSettingsMarketingUpdate,
    StoreSettingsResponse,
)
from app.schemas.ai import AiChatMessage, AiChatRequest, AiChatResponse

__all__ = [
    "BaseSchema",
    "StandardResponse",
    "PaginatedResponse",
    "RegisterStep1Request",
    "RegisterStep1Response",
    "VerifyOtpRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "CollaboratorCreate",
    "CollaboratorUpdate",
    "CollaboratorResponse",
    "ShopCreate",
    "ShopResponse",
    "StoreTemplateResponse",
    "StoreCustomizationUpdate",
    "StoreCustomizationResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "BulkStatusRequest",
    "OrderItemSchema",
    "PublicCheckoutRequest",
    "OrderUpdateStatusRequest",
    "OrderAssignDeliveryRequest",
    "OrderResponse",
    "RestockRequest",
    "ThresholdUpdateRequest",
    "InventoryItemResponse",
    "StockKpisResponse",
    "WalletSummaryResponse",
    "PayoutAccountCreate",
    "PayoutAccountResponse",
    "WithdrawRequest",
    "WalletTransactionResponse",
    "ChargeCreate",
    "ChargeResponse",
    "AccountingDashboardResponse",
    "ClientResponse",
    "WhatsAppCampaignCreate",
    "WhatsAppCampaignResponse",
    "SavedAudienceCreate",
    "SavedAudienceResponse",
    "AffiliateReferralResponse",
    "AffiliateSummaryResponse",
    "TransferCommissionRequest",
    "StoreSettingsGeneralUpdate",
    "StoreSettingsCodFormUpdate",
    "StoreSettingsMarketingUpdate",
    "StoreSettingsResponse",
    "AiChatMessage",
    "AiChatRequest",
    "AiChatResponse",
]


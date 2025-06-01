from typing import List, Optional
from datetime import date, time, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

# Base schemas
class ItemBase(BaseModel):
    item_name: str
    item_name_standardized: Optional[str] = None
    quantity: Decimal
    unit: Optional[str] = None
    unit_price_original: Optional[Decimal] = None
    unit_price_after_discount: Optional[Decimal] = None
    item_discount_amount: Optional[Decimal] = None
    item_total_price: Decimal
    vat_rate: Optional[str] = None
    ai_category: Optional[str] = None
    is_frozen: bool = False

class DiscountBase(BaseModel):
    discount_name: str
    discount_amount: Decimal

class VatSummaryBase(BaseModel):
    vat_rate: str
    base_amount: Decimal
    vat_amount: Decimal
    vat_percent: int

class UsedCouponBase(BaseModel):
    coupon_name: str
    coupon_value: Decimal

class ReceiptBase(BaseModel):
    store_name: str
    store_address: Optional[str] = None
    store_nip: Optional[str] = None
    purchase_date: date
    purchase_time: time
    total_amount: Decimal
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None
    register_number: Optional[str] = None
    loyalty_card_used: bool = False
    loyalty_card_savings: Optional[Decimal] = None

# Create schemas
class ItemCreate(ItemBase):
    pass

class DiscountCreate(DiscountBase):
    pass

class VatSummaryCreate(VatSummaryBase):
    pass

class UsedCouponCreate(UsedCouponBase):
    pass

class ReceiptCreate(ReceiptBase):
    items: List[ItemCreate]
    discounts: Optional[List[DiscountCreate]] = []
    vat_summaries: Optional[List[VatSummaryCreate]] = []
    used_coupons: Optional[List[UsedCouponCreate]] = []

# Read schemas
class Item(ItemBase):
    item_id: int
    receipt_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Discount(DiscountBase):
    discount_id: int
    receipt_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class VatSummary(VatSummaryBase):
    vat_id: int
    receipt_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UsedCoupon(UsedCouponBase):
    coupon_id: int
    receipt_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Receipt(ReceiptBase):
    receipt_id: int
    created_at: datetime
    items: List[Item]
    discounts: List[Discount]
    vat_summaries: List[VatSummary]
    used_coupons: List[UsedCoupon]

    class Config:
        from_attributes = True

# Update schemas
class ItemUpdate(ItemBase):
    pass

class DiscountUpdate(DiscountBase):
    pass

class VatSummaryUpdate(VatSummaryBase):
    pass

class UsedCouponUpdate(UsedCouponBase):
    pass

class ReceiptUpdate(BaseModel):
    store_name: Optional[str] = None
    store_address: Optional[str] = None
    store_nip: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_time: Optional[time] = None
    total_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    receipt_number: Optional[str] = None
    register_number: Optional[str] = None
    loyalty_card_used: Optional[bool] = None
    loyalty_card_savings: Optional[Decimal] = None

# List schemas
class ReceiptList(BaseModel):
    items: List[Receipt]
    total: int
    page: int
    size: int
    pages: int 
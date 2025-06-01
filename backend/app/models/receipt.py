from sqlalchemy import Boolean, Column, Integer, String, Float, Date, Time, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class Receipt(Base):
    __tablename__ = "receipts"

    receipt_id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(100), nullable=False)
    store_address = Column(String)
    store_nip = Column(String(20))
    purchase_date = Column(Date, nullable=False)
    purchase_time = Column(Time, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50))
    receipt_number = Column(String(50))
    register_number = Column(String(20))
    loyalty_card_used = Column(Boolean, default=False)
    loyalty_card_savings = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    items = relationship("Item", back_populates="receipt", cascade="all, delete-orphan")
    discounts = relationship("Discount", back_populates="receipt", cascade="all, delete-orphan")
    vat_summaries = relationship("VatSummary", back_populates="receipt", cascade="all, delete-orphan")
    used_coupons = relationship("UsedCoupon", back_populates="receipt", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.receipt_id"), nullable=False)
    item_name = Column(String, nullable=False)
    item_name_standardized = Column(String)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit = Column(String(20))
    unit_price_original = Column(Numeric(10, 2))
    unit_price_after_discount = Column(Numeric(10, 2))
    item_discount_amount = Column(Numeric(10, 2))
    item_total_price = Column(Numeric(10, 2), nullable=False)
    vat_rate = Column(String(1))
    ai_category = Column(String(100))
    is_frozen = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    receipt = relationship("Receipt", back_populates="items")

class Discount(Base):
    __tablename__ = "discounts"

    discount_id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.receipt_id"), nullable=False)
    discount_name = Column(String, nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    receipt = relationship("Receipt", back_populates="discounts")

class VatSummary(Base):
    __tablename__ = "vat_summary"

    vat_id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.receipt_id"), nullable=False)
    vat_rate = Column(String(1), nullable=False)
    base_amount = Column(Numeric(10, 2), nullable=False)
    vat_amount = Column(Numeric(10, 2), nullable=False)
    vat_percent = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    receipt = relationship("Receipt", back_populates="vat_summaries")

class UsedCoupon(Base):
    __tablename__ = "used_coupons"

    coupon_id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.receipt_id"), nullable=False)
    coupon_name = Column(String, nullable=False)
    coupon_value = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    receipt = relationship("Receipt", back_populates="used_coupons") 
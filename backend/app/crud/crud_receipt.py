from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.receipt import Receipt, Item, Discount, VatSummary, UsedCoupon
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate

class CRUDReceipt(CRUDBase[Receipt, ReceiptCreate, ReceiptUpdate]):
    def create(self, db: Session, *, obj_in: ReceiptCreate) -> Receipt:
        # Create receipt
        db_obj = Receipt(
            store_name=obj_in.store_name,
            store_address=obj_in.store_address,
            store_nip=obj_in.store_nip,
            purchase_date=obj_in.purchase_date,
            purchase_time=obj_in.purchase_time,
            total_amount=obj_in.total_amount,
            payment_method=obj_in.payment_method,
            receipt_number=obj_in.receipt_number,
            register_number=obj_in.register_number,
            loyalty_card_used=obj_in.loyalty_card_used,
            loyalty_card_savings=obj_in.loyalty_card_savings,
        )
        db.add(db_obj)
        db.flush()  # Get ID without committing

        # Create items
        for item in obj_in.items:
            db_item = Item(**item.dict(), receipt_id=db_obj.receipt_id)
            db.add(db_item)

        # Create discounts
        for discount in obj_in.discounts:
            db_discount = Discount(**discount.dict(), receipt_id=db_obj.receipt_id)
            db.add(db_discount)

        # Create VAT summaries
        for vat in obj_in.vat_summaries:
            db_vat = VatSummary(**vat.dict(), receipt_id=db_obj.receipt_id)
            db.add(db_vat)

        # Create used coupons
        for coupon in obj_in.used_coupons:
            db_coupon = UsedCoupon(**coupon.dict(), receipt_id=db_obj.receipt_id)
            db.add(db_coupon)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_with_filters(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 10,
        store_name: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Tuple[List[Receipt], int]:
        query = db.query(Receipt)

        # Apply filters
        if store_name:
            query = query.filter(Receipt.store_name.ilike(f"%{store_name}%"))
        if date_from:
            query = query.filter(Receipt.purchase_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            query = query.filter(Receipt.purchase_date <= datetime.strptime(date_to, "%Y-%m-%d").date())

        # Get total count
        total = query.count()

        # Apply pagination
        receipts = query.order_by(Receipt.purchase_date.desc()).offset(skip).limit(limit).all()

        return receipts, total

crud_receipt = CRUDReceipt(Receipt) 
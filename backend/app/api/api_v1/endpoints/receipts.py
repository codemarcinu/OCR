from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.receipt import Receipt, ReceiptCreate, ReceiptUpdate, ReceiptList
from app.crud import crud_receipt

router = APIRouter()

@router.post("/", response_model=Receipt)
def create_receipt(
    *,
    db: Session = Depends(deps.get_db),
    receipt_in: ReceiptCreate,
) -> Any:
    """
    Create new receipt with all related data.
    """
    receipt = crud_receipt.create(db=db, obj_in=receipt_in)
    return receipt

@router.get("/", response_model=ReceiptList)
def read_receipts(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    store_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Any:
    """
    Retrieve receipts with pagination and filtering.
    """
    receipts, total = crud_receipt.get_multi_with_filters(
        db=db,
        skip=skip,
        limit=limit,
        store_name=store_name,
        date_from=date_from,
        date_to=date_to,
    )
    return {
        "items": receipts,
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/{receipt_id}", response_model=Receipt)
def read_receipt(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
) -> Any:
    """
    Get receipt by ID.
    """
    receipt = crud_receipt.get(db=db, id=receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

@router.put("/{receipt_id}", response_model=Receipt)
def update_receipt(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
    receipt_in: ReceiptUpdate,
) -> Any:
    """
    Update receipt.
    """
    receipt = crud_receipt.get(db=db, id=receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    receipt = crud_receipt.update(db=db, db_obj=receipt, obj_in=receipt_in)
    return receipt

@router.delete("/{receipt_id}")
def delete_receipt(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
) -> Any:
    """
    Delete receipt.
    """
    receipt = crud_receipt.get(db=db, id=receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    crud_receipt.remove(db=db, id=receipt_id)
    return {"status": "success", "message": "Receipt deleted"} 
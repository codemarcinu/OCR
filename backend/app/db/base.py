# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base
from app.models.user import User
from app.models.receipt import Receipt, Item, Discount, VatSummary, UsedCoupon 
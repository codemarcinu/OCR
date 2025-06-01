import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.crud import crud_user
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


async def init_db(db: AsyncSession) -> None:
    try:
        # Create first superuser
        user = await crud_user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER_EMAIL,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
                full_name="Initial Admin"
            )
            user = await crud_user.create(db, obj_in=user_in)
            logger.info("Superuser created")
        else:
            logger.info("Superuser already exists")
            
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
        raise 
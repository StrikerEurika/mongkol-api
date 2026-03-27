from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl="/auth/login",
    authorizationUrl="/auth/login",
)

# Define role-based permissions
role_permissions = {
    UserRole.ADMIN: {
        "admin:all",  # Full admin access
        "sales:read",  # Read sales
        "sales:create",  # Create sales
        "sales:update",  # Update sales
        "sales:delete",  # Delete sales
        "products:read",  # Read products
        "products:create",  # Create products
        "products:update",  # Update products
        "products:delete",  # Delete products
        "users:read",  # Read users
        "users:update",  # Update users
        "staff:manage",  # Manage staff
    },
    UserRole.STAFF: {
        "sales:read",  # Read sales
        "sales:create",  # Create sales
        "sales:update_own",  # Update own sales
        "products:read",  # Read products
    },
}


def has_permission(user: User, permission: str) -> bool:
    """Check if a user has a specific permission."""
    permissions = role_permissions.get(user.role, set())
    return permission in permissions


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authentication Token",
            )
        user_id = int(user_id_str)

    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication Token",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not Found or Inactive",
        )
    return user


def require_permission(required_permission: str):
    async def permission_dependency(user: User = Depends(get_current_user)):
        if not has_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {required_permission} required",
            )
        return user

    return permission_dependency


# For backward compatibility, we define require_admin as requiring the "admin:all" permission
require_admin = require_permission("admin:all")

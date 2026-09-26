import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new clinical team member or system user.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{payload.email}' already exists"
        )

    user = User(
        name=payload.name,
        email=payload.email,
        role=payload.role,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created user '{user.name}' ({user.email})")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("", response_model=List[UserResponse], summary="List users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all registered clinical users.
    """
    return db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve user details by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.ssa_api_schemas import LoginRequest, LoginResponse
from app.database.crud import user as user_crud
from app.database.database import get_db

router = APIRouter()


@router.post("", response_model=LoginResponse)
async def login(input_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login API handling both:
    - Normal login (email + password)
    - SSO login (email + isSso = true, auto-creates user)

    Returns:
    - JWT token
    """
    # Ensure password is provided
    if not input_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required."
        )
    
    # Authenticate or auto-create user
    user = user_crud.authenticate_user(db, input_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password."
        )

    # Generate token
    token = user_crud.get_token(user.email)
    return LoginResponse(token=token)

import hashlib
import datetime
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, TOKEN_EXPIRY_IN_DAYS, ENCODING_ALGORITHM
from app.database.data_classes.ssa_models import User
from app.api.schemas.ssa_api_schemas import LoginRequest


# ---------------------------------------------------------------------
# Initialize Default Users
# ---------------------------------------------------------------------

def init_user(db: Session):
    """
    Initialize default user records (studio_admin and studio_user).
    This runs during application startup.
    """
    # Define default users
    default_users = [
        {
            "username": "studio_admin",
            "email": "studio_admin@elevancehealth.com",
            "password": hashlib.md5("admin@123".encode()).hexdigest(),  # or use stored hash
            "first_name": "Agent Studio",
            "last_name": "Admin",
            "user_role": "user",
            "group_id": "admin",
        },
        {
            "username": "studio_user",
            "email": "studio_user@elevancehealth.com",
            "password": hashlib.md5("user@123".encode()).hexdigest(),  # or use stored hash
            "first_name": "Agent Studio",
            "last_name": "User",
            "user_role": "user",
            "group_id": "user",
        },
    ]

    for u in default_users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            new_user = User(
                username=u["username"],
                email=u["email"],
                password=u["password"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                user_role=u["user_role"],
                date_created=datetime.datetime.utcnow(),
                group_id=u["group_id"],
                date_updated=None,
                date_expired=None,
            )
            db.add(new_user)
            db.commit()


# ---------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------
def encode_jwt_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=TOKEN_EXPIRY_IN_DAYS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ENCODING_ALGORITHM)
    return token


def get_token(email: str) -> str:
    return encode_jwt_token(email)


# ---------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares MD5 hash of plain text password with stored hashed password.
    """
    md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
    return md5_hash == hashed_password


def fetch_user(db: Session, email: str):
    """
    Returns user row or None.
    """
    return db.query(User).filter(
        User.email == email,
        User.date_expired.is_(None)
    ).first()


def update_user_login_timestamps(db: Session, email: str):
    """
    Updates login timestamps in DB.
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.last_login_date = user.current_login_date
        user.current_login_date = datetime.datetime.utcnow()
        db.commit()


# def add_user(db: Session, data: LoginRequest):
#     """
#     Creates new user ONLY during SSO login (no password).
#     """
#     new_user = User(
#         username=data.userId,
#         email=data.email,
#         password=None,
#         first_name=data.firstName,
#         last_name=data.lastName,
#         user_role="user",
#         date_created=datetime.datetime.utcnow(),
#         group_id=data.groupId
#     )
#     db.add(new_user)
#     db.commit()


# ---------------------------------------------------------------------
# Main Authentication Logic
# ---------------------------------------------------------------------
def authenticate_user(db: Session, login_data: LoginRequest):
    user = fetch_user(db, login_data.email)
    # print("#"*100)
    # print(user.email)
    # print(user.password)
    # print("#"*100)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate password
    if not login_data.password or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update login timestamps
    update_user_login_timestamps(db, login_data.email)

    return user
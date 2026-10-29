from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User
from utils.auth import hash_password
from api.schemas_auth import RegisterSchema, RegisterResponse
from utils.auth import verify_password
from utils.sessions import create_session
from fastapi.responses import JSONResponse
from api.schemas_login import LoginSchema, LoginResponse
from utils.current_user import current_user
from utils.sessions import delete_session
from fastapi import Request
from fastapi.responses import JSONResponse
from utils.oauth_google import oauth
from fastapi.responses import RedirectResponse
from utils.rate_limit import rate_limit


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterSchema, db: Session = Depends(get_db)):
    # Проверяем, есть ли пользователь
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Хешируем пароль
    password_hash = hash_password(payload.password)

    # Создаём пользователя
    user = User(
        email=payload.email,
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        status=user.status
    )

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginSchema, db: Session = Depends(get_db)):
    # Ищем пользователя
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Проверяем пароль
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Создаем session_id в redis
    session_id = await create_session(str(user.id))

    # Устанавливаем cookie
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,         # если будет https → ставим True
        samesite="lax",
        max_age=60*60*24*7
    )

    return response


@router.get("/me")
async def me(user=Depends(current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "status": user.status
    }



@router.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")

    if session_id:
        await delete_session(session_id)

    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("session_id")
    return response


@router.get("/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    google_id = userinfo["sub"]
    email = userinfo["email"]

    # ищем пользователя в БД
    user = db.query(User).filter(User.google_id == google_id).first()

    # если нет — создаём
    if not user:
        user = User(
            email=email,
            google_id=google_id,
            password_hash=None,  # пароля нет, логин только через Google
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # создаём сессию
    session_id = await create_session(str(user.id))

    response = RedirectResponse(url="/auth/me")
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60*60*24*7,
    )

    return response
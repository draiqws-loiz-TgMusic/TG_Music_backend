from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import uuid4
import jwt
import datetime
import sqlite3
from contextlib import contextmanager
import hashlib

router = APIRouter()

SECRET_KEY = "your-secret-key"  # Замените на свой секретный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserCreate(BaseModel):
    login: str
    password: str

@contextmanager
def get_db_connection():
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()
    try:
        yield con, cur
    finally:
        con.commit()
        con.close()

def create_users_table(cur):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            login TEXT UNIQUE,
            password TEXT
        );
    ''')

def hash_password(password):
    # Используем hashlib для хеширования паролей
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends()):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise credentials_exception
    with get_db_connection() as (con, cur):
        cur.execute("SELECT id, login FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        if user is None:
            raise credentials_exception
        return {"id": user[0], "login": user[1]}

@router.post("/registration/")
async def register_user(user: UserCreate):
    login = user.login
    password = user.password
    hashed_password = hash_password(password)
    try:
        with get_db_connection() as (con, cur):
            create_users_table(cur)
            cur.execute("SELECT login FROM users WHERE login = ?", (login,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")
            user_id = str(uuid4())
            cur.execute("INSERT INTO users (id, login, password) VALUES (?, ?, ?)", (user_id, login, hashed_password))
        return {"status": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/authorization/")
async def login_user(user: UserCreate):
    login = user.login
    password = user.password
    try:
        with get_db_connection() as (con, cur):
            cur.execute("SELECT id, password FROM users WHERE login = ?", (login,))
            db_user = cur.fetchone()
            if not db_user:
                raise HTTPException(status_code=400, detail="Incorrect login or password")
            user_id, hashed_password = db_user
            if not verify_password(password, hashed_password):
                raise HTTPException(status_code=400, detail="Incorrect login or password")
            access_token = create_access_token(data={"sub": user_id})
            return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-info/")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {"login": current_user["login"]}

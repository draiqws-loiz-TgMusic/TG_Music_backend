from fastapi import APIRouter, HTTPException
from uuid import uuid4
import jwt
import datetime
import sqlite3
from contextlib import contextmanager

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

router = APIRouter()

@contextmanager
def get_db_connection():
    try:
        con = sqlite3.connect('db.sqlite')
        cur = con.cursor()
        yield con, cur
    finally:
        con.commit()
        con.close()

def create_users_table(cur):
    cur.execute('''
                CREATE TABLE IF NOT EXISTS users(
                id TEXT PRIMARY KEY,
                login TEXT UNIQUE,
                password TEXT);
                '''
    )

def generate_token(password):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
        'iat': datetime.datetime.utcnow(),
        'sub': password
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def check_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/registration/")
async def new_user(login: str, password: str):
    try:
        with get_db_connection() as (con, cur):
            create_users_table(cur)
            cur.execute("SELECT login FROM users WHERE login = ?", (login,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")

            new_uuid = str(uuid4())
            password_token = generate_token(password)
            cur.execute("INSERT INTO users (id, login, password) VALUES (?, ?, ?)", (new_uuid, login, password_token))
        return {"status": f"User {login} successfully registered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/authorization/")
async def old_user(login: str, password: str):
    try:
        with get_db_connection() as (con, cur):
            cur.execute("SELECT password FROM users WHERE login = ?", (login,))
            db_password = cur.fetchone()

            if not db_password:
                raise HTTPException(status_code=400, detail="User does not exist")

            if password == check_token(db_password[0]):
                return {"status": "Successfully logged in"}
            else:
                raise HTTPException(status_code=401, detail="Incorrect credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

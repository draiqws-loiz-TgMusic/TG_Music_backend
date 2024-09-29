from fastapi import APIRouter, HTTPException
from uuid import uuid4
import jwt
import datetime
import sqlite3
from contextlib import contextmanager
from app.schemas import UserRegistration


SECRET_KEY = "draiqws_loiz"
ALGORITHM = "HS256"

router = APIRouter()

# работа с бд пользователей
@contextmanager
def get_db_connection():
    con = sqlite3.connect('db.sqlite')
    try:
        cur = con.cursor()
        yield con, cur
    finally:
        con.commit()
        con.close()

def create_users_table(cur):
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS Users(
            id TEXT PRIMARY KEY,
            login TEXT UNIQUE,
            password TEXT,
            JWTByLogin TEXT
        );
        '''
    )

def generate_token(username):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=100),
        'iat': datetime.datetime.utcnow(),
        'sub': username,
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
async def new_user(user: UserRegistration):
    login = user.login
    password = user.password
    try:
        with get_db_connection() as (con, cur):
            create_users_table(cur)
            cur.execute("SELECT login FROM Users WHERE login = ?", (login,))  #login
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")

            new_uuid = str(uuid4())
            JWTByLogin_token = generate_token(login)
            cur.execute(
                "INSERT INTO Users (id, login, password, JWTByLogin) VALUES (?, ?, ?, ?)", 
                (new_uuid, login, password, JWTByLogin_token)
            )
        return {"status": f"User {login} successfully registered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/login/")
async def old_user(user: UserRegistration):
    login = user.login
    password = user.password
    try:
        with get_db_connection() as (con, cur):
            cur.execute("SELECT password FROM Users WHERE login = ?", (login,))  #password
            db_password = cur.fetchone()[0]
            cur.execute("SELECT JWTByLogin FROM Users WHERE login = ?", (login,))  #JWT
            db_JWT= cur.fetchone()[0]
            if not db_password:
                raise HTTPException(status_code=400, detail="User doesn`t registr")
            # return {password, db_password}
            if str(password) == str(db_password):
                return {"status": "Successfully logged in", "token": db_JWT}
            else:
                raise HTTPException(status_code=401, detail="Incorrect password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
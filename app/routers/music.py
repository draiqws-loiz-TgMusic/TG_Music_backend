from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from uuid import uuid4
import sqlite3
from contextlib import contextmanager
import os
from .auth import get_current_user

router = APIRouter()

UPLOAD_DIRECTORY = "uploaded_music"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@contextmanager
def get_db_connection():
    con = sqlite3.connect('db.sqlite')
    cur = con.cursor()
    try:
        yield con, cur
    finally:
        con.commit()
        con.close()

def create_music_table(cur):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS music(
            id TEXT PRIMARY KEY,
            file_path TEXT,
            author TEXT,
            name TEXT,
            genre TEXT
        );
    ''')

class MusicCreate(BaseModel):
    author: str
    name: str
    genre: str

@router.post("/add-music/")
async def add_music(
    author: str,
    name: str,
    genre: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_db_connection() as (con, cur):
            create_music_table(cur)
            music_id = str(uuid4())
            filename = f"{music_id}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)

            # Сохранение файла
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            cur.execute('''
                INSERT INTO music (id, file_path, author, name, genre)
                VALUES (?, ?, ?, ?, ?);
            ''', (music_id, file_path, author, name, genre))

        return {"status": "Music added successfully", "music_id": music_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-music/")
async def get_music(genre: str = None):
    try:
        with get_db_connection() as (con, cur):
            create_music_table(cur)
            if genre:
                cur.execute("SELECT id, author, name, genre FROM music WHERE genre = ?", (genre,))
            else:
                cur.execute("SELECT id, author, name, genre FROM music")
            music_list = cur.fetchall()
            music = [{"id": m[0], "author": m[1], "name": m[2], "genre": m[3]} for m in music_list]
        return {"music": music}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/music/{music_id}")
async def download_music(music_id: str):
    try:
        with get_db_connection() as (con, cur):
            cur.execute("SELECT file_path FROM music WHERE id = ?", (music_id,))
            result = cur.fetchone()
            if result:
                file_path = result[0]
                if os.path.exists(file_path):
                    return FileResponse(path=file_path, media_type='audio/mpeg', filename=os.path.basename(file_path))
                else:
                    raise HTTPException(status_code=404, detail="File not found")
            else:
                raise HTTPException(status_code=404, detail="Music not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

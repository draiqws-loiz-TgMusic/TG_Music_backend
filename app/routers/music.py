from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from contextlib import contextmanager
import sqlite3

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

def create_table(cur):
    cur.execute('''
                CREATE TABLE IF NOT EXISTS music(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                music TEXT,
                author TEXT,
                name TEXT,
                genre TEXT);
                '''
    )

@router.post("/add-music/")
async def add_music(music: str, author: str, name: str, genre: str):
    try:
        with get_db_connection() as (con, cur):
            create_table(cur)
            cur.execute('''
                        INSERT INTO music(music, author, name, genre)
                        VALUES (?, ?, ?, ?);
                        ''', (music, author, name, genre))
        return {"status": "Music added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-music/")
async def get_music(genre: str):
    try:
        with get_db_connection() as (con, cur):
            cur.execute('''
                        SELECT * FROM music WHERE genre = ?;
                        ''', (genre,))
            music = cur.fetchall()
        return {"music": music}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio-player", response_class=HTMLResponse)
async def audio_player():
    try:
        with open("app/templates/audio_player.html", "r") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

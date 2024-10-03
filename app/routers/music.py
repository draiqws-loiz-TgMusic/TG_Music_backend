from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from contextlib import contextmanager
import sqlite3
from app.schemas import Music_play, Genre, Name

router = APIRouter()

# работа с бд музыкой
@contextmanager
def get_db_connection():
    try:
        con = sqlite3.connect('db.sqlite')
        cur = con.cursor()
        
        yield con, cur
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    finally:
        con.commit()
        con.close()

def create_table(cur):
    try:
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS music(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    author TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    src TEXT NOT NULL);
                    '''
        )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Error creating table: {str(e)}")

@router.post("/add-music/")
async def add_music(music: Music_play):
    try:
        with get_db_connection() as (con, cur):
            create_table(cur)
            cur.execute(
                '''
                INSERT INTO music(name, author, genre, src)
                VALUES (?, ?, ?, ?);
                ''', 
                (music.name, music.author, music.genre, music.src))
        return {"status": "Music added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-music-by-genre/")
async def get_music(genre: str):
    try:
        music = []
        with get_db_connection() as (con, cur):
            cur.execute(
                '''
                SELECT * 
                FROM music
                WHERE genre = ?;
                ''',
                (genre, ))
            music  = cur.fetchall()
        if not music:
            raise HTTPException(status_code=404, detail="No music found")
        return music
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get-music-all/")
async def get_music():
    try:
        music = []
        with get_db_connection() as (con, cur):
            cur.execute(
                '''
                SELECT * 
                FROM music
                ''',)
            music  = cur.fetchall()
        if not music:
            raise HTTPException(status_code=404, detail="No music found")
        return music
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

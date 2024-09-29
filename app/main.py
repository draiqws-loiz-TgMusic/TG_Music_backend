from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import music, auth

app = FastAPI()

# Настройка CORS для взаимодействия с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React фронтенд будет на этом порту
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(music.router)
app.include_router(auth.router)

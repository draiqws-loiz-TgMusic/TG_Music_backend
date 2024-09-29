from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI()

# Разрешаем запросы с адреса фронтенда
origins = [
    "http://localhost:3000",  # URL, на котором работает React
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешаем запросы с этого адреса
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем любые методы HTTP (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешаем любые заголовки
)

@app.get("/s")
def read_root():
    return {"message": "Welcome to the music service backend!"}

app.include_router(auth.router)

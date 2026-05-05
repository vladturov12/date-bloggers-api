from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Дэйт: Блогеры API")

# Разрешаем твоему фронтенду обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Временные данные прямо в коде (потом заменим на базу)
BLOGGERS = [
    {
        "id": 1,
        "name": "Анна Соколова",
        "username": "@anna_lifestyle",
        "followers": 425000,
        "er": 5.5,
        "status": "active",
    },
    {
        "id": 2,
        "name": "Максим Петров",
        "username": "@max_tech",
        "followers": 565000,
        "er": 8.7,
        "status": "active",
    },
    {
        "id": 3,
        "name": "Дмитрий Волков",
        "username": "@volkov_food",
        "followers": 1580000,
        "er": 4.15,
        "status": "active",
    },
]


@app.get("/")
def hello():
    return {"status": "ok", "message": "Дэйт: Блогеры API работает"}


@app.get("/bloggers")
def get_bloggers():
    return {"bloggers": BLOGGERS, "total": len(BLOGGERS)}


@app.get("/bloggers/{blogger_id}")
def get_blogger(blogger_id: int):
    for b in BLOGGERS:
        if b["id"] == blogger_id:
            return b
    return {"error": "Не найден"}

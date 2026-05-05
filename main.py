import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel

# === НАСТРОЙКА БАЗЫ ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# Railway даёт URL начинающийся с postgres://, а SQLAlchemy ждёт postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# === МОДЕЛЬ БЛОГЕРА В БАЗЕ ===
class Blogger(Base):
    __tablename__ = "bloggers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    followers = Column(Integer, default=0)
    er = Column(Float, default=0.0)
    status = Column(String, default="active")


# Создаём таблицы при запуске
Base.metadata.create_all(bind=engine)


# === ВХОДНЫЕ ДАННЫЕ ===
class BloggerCreate(BaseModel):
    name: str
    username: str
    followers: int = 0
    er: float = 0.0
    status: str = "active"


# === ПРИЛОЖЕНИЕ ===
app = FastAPI(title="Дэйт: Блогеры API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === ЭНДПОИНТЫ ===
@app.get("/")
def hello():
    return {"status": "ok", "message": "Дэйт: Блогеры API работает"}


@app.get("/bloggers")
def get_bloggers():
    db = SessionLocal()
    try:
        bloggers = db.query(Blogger).all()
        return {
            "bloggers": [
                {
                    "id": b.id,
                    "name": b.name,
                    "username": b.username,
                    "followers": b.followers,
                    "er": b.er,
                    "status": b.status,
                }
                for b in bloggers
            ],
            "total": len(bloggers),
        }
    finally:
        db.close()


@app.get("/bloggers/{blogger_id}")
def get_blogger(blogger_id: int):
    db = SessionLocal()
    try:
        b = db.query(Blogger).filter(Blogger.id == blogger_id).first()
        if not b:
            raise HTTPException(status_code=404, detail="Блогер не найден")
        return {
            "id": b.id,
            "name": b.name,
            "username": b.username,
            "followers": b.followers,
            "er": b.er,
            "status": b.status,
        }
    finally:
        db.close()


@app.post("/bloggers")
def create_blogger(data: BloggerCreate):
    db = SessionLocal()
    try:
        new_blogger = Blogger(**data.model_dump())
        db.add(new_blogger)
        db.commit()
        db.refresh(new_blogger)
        return {
            "id": new_blogger.id,
            "name": new_blogger.name,
            "username": new_blogger.username,
            "followers": new_blogger.followers,
            "er": new_blogger.er,
            "status": new_blogger.status,
        }
    finally:
        db.close()


@app.delete("/bloggers/{blogger_id}")
def delete_blogger(blogger_id: int):
    db = SessionLocal()
    try:
        b = db.query(Blogger).filter(Blogger.id == blogger_id).first()
        if not b:
            raise HTTPException(status_code=404, detail="Блогер не найден")
        db.delete(b)
        db.commit()
        return {"status": "deleted", "id": blogger_id}
    finally:
        db.close()


# === НАЧАЛЬНОЕ ЗАПОЛНЕНИЕ ===
@app.post("/seed")
def seed():
    """Заполнить базу тестовыми данными (запускать вручную один раз)"""
    db = SessionLocal()
    try:
        if db.query(Blogger).count() > 0:
            return {"message": "База уже заполнена"}

        seed_data = [
            Blogger(name="Анна Соколова", username="@anna_lifestyle", followers=425000, er=5.5),
            Blogger(name="Максим Петров", username="@max_tech", followers=565000, er=8.7),
            Blogger(name="Дмитрий Волков", username="@volkov_food", followers=1580000, er=4.15),
        ]
        for b in seed_data:
            db.add(b)
        db.commit()
        return {"message": f"Добавлено {len(seed_data)} блогеров"}
    finally:
        db.close()

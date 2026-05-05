import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Blogger, Base

logging.basicConfig(level=logging.INFO)

# === НАСТРОЙКА ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# === ОПРЕДЕЛЕНИЕ ПЛАТФОРМЫ И USERNAME ИЗ ССЫЛКИ ===
def parse_link(text: str):
    """Возвращает (platform, username) или None"""
    text = text.strip()

    patterns = [
        ("instagram", r"(?:instagram\.com|instagr\.am)/([A-Za-z0-9_.]+)"),
        ("youtube",   r"youtube\.com/(?:@|c/|channel/|user/)([A-Za-z0-9_.\-]+)"),
        ("youtube",   r"youtu\.be/([A-Za-z0-9_.\-]+)"),
        ("tiktok",    r"tiktok\.com/@([A-Za-z0-9_.]+)"),
        ("telegram",  r"(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)"),
        ("vk",        r"vk\.com/([A-Za-z0-9_.]+)"),
    ]

    for platform, pattern in patterns:
        m = re.search(pattern, text)
        if m:
            username = m.group(1)
            # Чистим хвосты типа ?utm_source=...
            username = username.split("?")[0].split("/")[0]
            return platform, username
    return None


# === ХЭНДЛЕРЫ ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Я бот «Дэйт: Блогеры». Кидай мне ссылку на блогера — добавлю в базу.\n\n"
        "Поддерживаю: Instagram, YouTube, TikTok, Telegram, VK\n\n"
        "Например:\n"
        "https://instagram.com/anna_lifestyle\n"
        "https://t.me/max_tech\n\n"
        "Команды:\n"
        "/list — показать всех блогеров в базе"
    )


@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    db = SessionLocal()
    try:
        bloggers = db.query(Blogger).all()
        if not bloggers:
            await message.answer("База пока пустая. Кинь ссылку на блогера!")
            return

        text = f"📋 Блогеров в базе: {len(bloggers)}\n\n"
        for b in bloggers:
            text += f"• {b.name} ({b.username})\n"
        await message.answer(text)
    finally:
        db.close()


@dp.message()
async def handle_link(message: types.Message):
    text = message.text or ""
    parsed = parse_link(text)

    if not parsed:
        await message.answer(
            "Не похоже на ссылку 🤔\n\n"
            "Поддерживаю: Instagram, YouTube, TikTok, Telegram, VK"
        )
        return

    platform, username = parsed
    full_username = f"@{username}"

    db = SessionLocal()
    try:
        # Проверка дубликата
        existing = db.query(Blogger).filter(Blogger.username == full_username).first()
        if existing:
            await message.answer(
                f"⚠️ Блогер {full_username} уже есть в базе.\n"
                f"Имя: {existing.name}"
            )
            return

        # Добавляем
        new_blogger = Blogger(
            name=username,  # пока используем username как имя — позже подтянем настоящее
            username=full_username,
            followers=0,
            er=0.0,
            status="in_progress",
        )
        db.add(new_blogger)
        db.commit()
        db.refresh(new_blogger)

        await message.answer(
            f"✅ Блогер добавлен в базу!\n\n"
            f"Платформа: {platform}\n"
            f"Username: {full_username}\n"
            f"ID: {new_blogger.id}\n\n"
            f"Открой приложение, чтобы заполнить остальные данные."
        )
    finally:
        db.close()


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

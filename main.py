import asyncio
from loader import dp, bot
from fastapi import FastAPI, Request
from aiogram import types
from loader import app
from config import domen, port
import uvicorn



WEBHOOK_HOST = f'https://{domen}'  # Webhook URL manzili
WEBHOOK_PATH = '/webhook'  # Webhook endpoint
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH
# FastAPI endpointlari
@app.get("/status")
async def get_status():
    return {"status": "Bot ishlayapti!"}

@app.post("/webhook")
async def webhook(request: Request):
    json = await request.json()
    update = types.Update(**json)
    await dp.feed_webhook_update(bot=bot, update=update)
    return {"status": "ok"}

# Botni webhook rejimida ishga tushirish
async def on_start():
    # Webhookni o'rnatish
    await bot.set_webhook(WEBHOOK_URL)

# FastAPI va Aiogram parallel ishga tushirish
async def uvicorn_server():
    """FastAPI serverini ishga tushirish"""
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()  # `async` rejimda ishlatish

async def main():
    bot_task = asyncio.create_task(on_start())  # Botni webhook rejimida ishga tushirish
    api_task = asyncio.create_task(uvicorn_server())  # FastAPI serverini ishga tushirish
    await asyncio.gather(bot_task, api_task)  # Ikkisini parallel ishlatish

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

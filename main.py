import asyncio
import random
import string
import re
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import os

BOT_TOKEN = "7631663395:AAFItyBLpVoFrNX1Eoa5gOK8wOeAG0OlkI0"
API_KEY = "5VmjtebU6s3yWnwAELSd"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

domains = [
    "priyomail.us",
    "priyomail.in",
    "priyomail.uk",
    "priyomail.top",
    "priyo-mail.com"
]

def generate_random_username():
    letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(7))
    numbers = ''.join(random.choice(string.digits) for _ in range(4))
    return f"Ph.{letters}{numbers}"

async def create_email(domain):
    url = f"https://api.priyo.email/api/change/{API_KEY}"
    headers = {
        "user-agent": "Dart/3.6 (dart:io)",
        "content-type": "application/json; charset=utf-8",
        "accept": "application/json"
    }

    for attempt in range(3):
        username = generate_random_username()
        data = {"username": username, "domain": domain}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                response = await resp.json()

        print(f"[Attempt {attempt+1}] Create email response: {response}")

        if response.get("success"):
            email_resp = response.get("email")
            email_resp = "P" + email_resp[1:]  # force uppercase P at start
            return email_resp

        await asyncio.sleep(0.5)

    return None

async def check_inbox(email):
    url = f"https://api.priyo.email/api/messages/{email}/{API_KEY}"
    headers = {
        "user-agent": "Dart/3.6 (dart:io)",
        "content-type": "application/json",
        "accept": "application/json"
    }

    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                messages = await resp.json()

        if messages:
            for msg in messages:
                if msg.get("sender_email") == "no-reply@philcoin.io":
                    content = msg.get("content", "")
                    link = extract_verification_link(content)
                    if link != "No verification link found.":
                        return link
        await asyncio.sleep(0.5)

def extract_verification_link(html):
    match = re.search(r'(https:\/\/philsocial-auth-prod[^\s\'">]+)', html)
    return match.group(1) if match else "No verification link found."

async def verify_email(link):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            status = resp.status
            print(f"Verification link GET status: {status}")
    return status == 200

@dp.message(Command("create_mail"))
async def handle_create_mail(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=domain, callback_data=domain)] for domain in domains
    ])

    await message.answer("Select mail domain:", parse_mode=ParseMode.HTML, reply_markup=keyboard)
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    welcome_text = (
        "👋 Welcome to the <b>PhilSocial Email Bot</b>!\n\n"
        "With this bot, you can quickly generate temporary email addresses for PhilSocial account verification.\n\n"
        "📩 To get started, command <b>click here </b>👇\n"
        "<b>/create_mail</b>\n\n"
        "We'll handle the rest — from email creation to inbox checking and automatic verification. ✅\n\n"
        "If you have any issues, feel free to reach out to the admin.\n\n"
        "Enjoy! 🚀"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.HTML)
@dp.callback_query()
async def handle_domain_selection(callback: types.CallbackQuery):
    domain = callback.data
    await callback.message.edit_text(f"Generating email with domain {domain}...", parse_mode=ParseMode.HTML)

    email = await create_email(domain)
    if not email:
        await callback.message.edit_text("Failed to create email after 3 attempts. Please contact admin to update API.")
        return

    await callback.message.edit_text(f"PhilSocial Mail [1-Tap Copy]\n\n<code>{email}</code>", parse_mode=ParseMode.HTML)

    link = await check_inbox(email)
    if link:
        verified = await verify_email(link)
        if verified:
            await callback.message.answer("Email verification complete!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
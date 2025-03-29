import os
import discord
from discord.ext import commands
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Храним варны в памяти (для полноценного хранения лучше использовать БД)
warnings = {}

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Без причины"):
    """Выдаёт варн и снимает указанную роль"""
    if member.id not in warnings:
        warnings[member.id] = []
    warnings[member.id].append(reason)

    # Роль, которую нужно снять (замени на ID нужной роли)
    role_id = 1355233773045678253  # <-- Заменить на реальный ID роли
    role = discord.utils.get(member.guild.roles, id=role_id)

    if role and role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"🚨 {member.mention} получил варн! Роль {role.name} снята.\nПричина: {reason}")
    else:
        await ctx.send(f"🚨 {member.mention} получил варн, но у него нет нужной роли.\nПричина: {reason}")

@bot.command()
async def ask(ctx, *, question):
    """Отправляет запрос к DeepSeek и отвечает в чат"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": question}]}

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        answer = response.json()["choices"][0]["message"]["content"]
        await ctx.send(f"**Ответ:** {answer}")
    else:
        await ctx.send("Ошибка при запросе к DeepSeek 😔")

bot.run(TOKEN)

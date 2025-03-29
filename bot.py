import discord
from discord.ext import commands
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # Берём токен из переменных окружения
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Ключ от DeepSeek

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

warns = {}  # Словарь для хранения предупреждений

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")

@bot.command()
async def ask(ctx, *, query):
    """Команда для обращения к нейросети"""
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": query}]},
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    )
    answer = response.json().get("choices", [{}])[0].get("message", {}).get("content", "Ошибка при получении ответа.")
    await ctx.send(answer)

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Не указана"):
    """Команда для выдачи варна"""
    if member.id not in warns:
        warns[member.id] = []
    warns[member.id].append(reason)

    # Удаляем указанную роль (замени "RoleName" на нужную)
    role = discord.utils.get(ctx.guild.roles, name="RoleName")
    if role and role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} получил варн! Причина: {reason}. Роль {role.name} удалена.")
    else:
        await ctx.send(f"{member.mention} получил варн! Причина: {reason}.")

bot.run(TOKEN)

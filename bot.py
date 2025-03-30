import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
import random

app = Flask(__name__)

# Список пафосных фраз для ответа на упоминание
GREETING_PHRASES = [
    "Я — страж порядка. Не тревожьте меня без дела.",
    "Модерация — мой долг. Что вам угодно?",
    "Порядок и справедливость — вот мои принципы. Чем могу помочь?",
    "Законы сервера — моя обязанность. Какие вопросы?",
    "Я наблюдаю за каждым вашим шагом. Зачем вы позвали меня?",
    "Нарушители будут наказаны. Что-то случилось?",
    "Босс, я слушаю вас. Но не злоупотребляйте моим вниманием.",
]

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run, daemon=True).start()

# Словарь для хранения предупреждений (можно заменить на базу данных)
warnings = {}

# Указываем префикс команды и intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Для работы с ролями и участниками

bot = commands.Bot(command_prefix="~", intents=intents)
    
# Обработчик события запуска бота
@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")
    
# Реакция на упоминание бота
@bot.event
@commands.has_any_role("Администратор", "БОСС")
async def on_message(message):
    # Игнорируем сообщения от самого бота
    if message.author == bot.user:
        return

    # Проверяем, упоминается ли бот в сообщении
    if bot.user.mentioned_in(message):
        # Выбираем случайную фразу из списка
        response = random.choice(GREETING_PHRASES)
        await message.channel.send(response)

    # Обрабатываем другие команды
    await bot.process_commands(message)
    
# Команда "угроза"
@bot.command(name="угроза")
@commands.has_permissions(manage_roles=True)  # Только пользователи с правами управления ролями могут использовать команду
async def warn(ctx, member: discord.Member, *, reason: str):
    # Проверяем, существует ли роль, которую нужно снять
    role_name = "тестовая роль"  # Замените на название роли, которую хотите снять
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        await ctx.send(f"Роль '{role_name}' не найдена на сервере.")
        return

    try:
        # Снимаем роль
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"Роль '{role_name}' успешно снята с пользователя {member.display_name}.")
        else:
            await ctx.send(f"У пользователя {member.display_name} нет роли '{role_name}'.")
    except discord.Forbidden:
        await ctx.send("У бота недостаточно прав для снятия роли. Проверьте права бота и иерархию ролей.")
        return

    # Добавляем предупреждение
    if member.id not in warnings:
        warnings[member.id] = []
    warnings[member.id].append(reason)

    # Отправляем сообщение о предупреждении
    await ctx.send(f"Пользователь {member.display_name} получил предупреждение. Причина: {reason}")

    # Проверяем количество предупреждений
    if len(warnings[member.id]) >= 2:
        try:
            await member.ban(reason="Накоплено 2 или более предупреждений.")
            await ctx.send(f"Пользователь {member.display_name} был забанен за накопление 2 или более предупреждений.")
        except discord.Forbidden:
            await ctx.send("У бота недостаточно прав для бана пользователя.")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при попытке бана: {e}")

# Команда "списокугроз"
@bot.command(name="списокугроз")
@commands.has_any_role("Администратор", "БОСС")
async def list_all_warnings(ctx):
    if not warnings:
        await ctx.send("На сервере ещё не выдано ни одного предупреждения.")
        return
    # Формируем список всех предупреждений
    all_warnings = []
    for user_id, reasons in warnings.items():
        member = ctx.guild.get_member(user_id)
        member_name = member.display_name if member else f"Пользователь ID:{user_id} (покинул сервер)"
        warning_list = "\n".join([f"  - {reason}" for reason in reasons])
        all_warnings.append(f"{member_name}:\n{warning_list}")

    # Отправляем результат
    result = "Все выданные предупреждения на сервере:\n" + "\n".join(all_warnings)
    await ctx.send(result)
    
# Команда "команды"
@bot.command(name="команды")
@commands.has_any_role("Администратор", "БОСС")
async def list_of_commands(ctx):
    """Выводит список всех доступных команд бота."""
    # Собираем список команд
    command_list = [f"~{command.name}" for command in bot.commands]
    commands_text = ", ".join(command_list)
    
    # Отправляем сообщение с командами
    await ctx.send(f"Доступные команды: {commands_text}")
    
# Обработка ошибок доступа
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("У вас нет прав для выполнения этой команды. Требуемые роли: 'админ' или 'босс'.")
    else:
        await ctx.send(f"Произошла ошибка: {error}")
        
TOKEN = os.getenv("DISCORD_TOKEN")
# Запуск бота
if __name__ == "__main__":
    bot.run(TOKEN)

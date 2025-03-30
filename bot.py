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
    """Выдаёт варн игроку. При достижении 2-х варнов - банит"""
    # Проверяем, существует ли роль, которую нужно снять
    role_name1 = "Водитель"  # Замените на название роли, которую хотите снять
    role1 = discord.utils.get(ctx.guild.roles, name=role_name1)
    role_name2 = "Новичок"  # Замените на название роли, которую хотите снять
    role2 = discord.utils.get(ctx.guild.roles, name=role_name2)

    if not role1:
        await ctx.send(f"Роль '{role_name1}' не найдена на сервере.")
        return
    if not role2:
        await ctx.send(f"Роль '{role_name2}' не найдена на сервере.")
        return
    try:
        # Снимаем роль
        if role1 in member.roles:
            await member.remove_roles(role1)
            await ctx.send(f"Роль '{role_name1}' успешно снята с пользователя {member.display_name}.")
            await member.add_roles(role2)
            await ctx.send(f"Роль '{role_name2}' успешно добавлена пользователю {member.display_name}.")
        else:
            await ctx.send(f"У пользователя {member.display_name} нет роли '{role_name1}'.")
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
            await member.ban(reason="Накоплено 2 предупреждения.")
            await ctx.send(f"Пользователь {member.display_name} был забанен за накопление 2-х предупреждений.")
        except discord.Forbidden:
            await ctx.send("У бота недостаточно прав для бана пользователя.")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при попытке бана: {e}")

# Команда "списокугроз"
@bot.command(name="списокугроз")
@commands.has_any_role("Администратор", "БОСС")
async def list_all_warnings(ctx):
    """Выводит список всех выданных варнов"""
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

@bot.command(name="удалитьварны")
@commands.has_any_role("Администратор", "БОСС")  # Только админы и боссы могут использовать команду
async def remove_warnings_and_update_roles(ctx, members: commands.Greedy[discord.Member]):
    """
    Удаляет предупреждения у указанных пользователей и обновляет их роли.
    Пример использования: ~удалитьварны Username1 Username2
    """
    if not members:
        await ctx.send("Укажите хотя бы одного пользователя.")
        return

    results = []  # Список результатов для каждого пользователя

    for member in members:
        # Удаляем предупреждение, если оно есть
        if member.id in warnings and warnings[member.id]:
            removed_warning = warnings[member.id].pop(0)  # Удаляем первое предупреждение
            results.append(f"У пользователя {member.display_name} удалено предупреждение: {removed_warning}")
        else:
            results.append(f"У пользователя {member.display_name} нет предупреждений.")

        # Проверяем роли
        водитель_role = discord.utils.get(ctx.guild.roles, name="Водитель")
        новичок_role = discord.utils.get(ctx.guild.roles, name="Новичок")

        if водитель_role and новичок_role:
            if водитель_role not in member.roles and новичок_role in member.roles:
                try:
                    await member.add_roles(водитель_role)
                    await member.remove_roles(новичок_role)
                    results.append(f"Пользователю {member.display_name} выдана роль 'Водитель' и снята роль 'Новичок'.")
                except discord.Forbidden:
                    results.append(f"У бота недостаточно прав для изменения ролей у {member.display_name}.")
                except Exception as e:
                    results.append(f"Произошла ошибка при изменении ролей у {member.display_name}: {e}")
        else:
            results.append(f"Роли 'Водитель' или 'Новичок' не найдены на сервере.")

    # Отправляем результаты
    await ctx.send("\n".join(results))
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

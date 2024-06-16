import logging
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import telebot
from Config import Config
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

CODESTRAL_API_URL = 'https://codestral.mistral.ai/v1'

CODESTRAL_API_KEY = Config.CODESTRAL_API_KEY
TELEGRAM_TOKEN = Config.TELEGRAM_TOKEN
bot = telebot.TeleBot(TELEGRAM_TOKEN)




# Настройка ведения журнала
logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка сообщения при команде /start ."""
    user = update.effective_user
    await update.message.reply_text(
        f'Привет, {user.first_name}! Я могу писать или исправлять код, просто напиши мне задачу. Для справки нажми /help. ')
    logger.info(f"Пользователь {user.id} {user.first_name} отправил команду: /start")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка сообщения при команде /help ."""
    user = update.effective_user
    await update.message.reply_text('Данный бот работает с Codestral API - языковой моделью, специализированной на'
                                    ' создании и изменении кода. Проект французской компании Mistral AI. Разработчик бота Сергей З.')
    logger.info(f"Пользователь {user.id} {user.first_name} отправил команду /help")


"""Создаем словарь для контекста"""
chat_context = {}


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик сообщений пользователя."""

    client = MistralClient(api_key=CODESTRAL_API_KEY)
    model = "codestral-latest"

    user_message = update.message.text

    """Получаем идентификатор чата"""
    chat_id = update.effective_chat.id

    """Если контекст диалога для этого чата уже существует, добавляем новое сообщение пользователя к нему"""
    if chat_id in chat_context:
        chat_context[chat_id].append(ChatMessage(role="user", content=user_message))
    else:
        """ Если контекста диалога для этого чата еще нет, создаем новый список сообщений"""
        chat_context[chat_id] = [ChatMessage(role="user", content=user_message)]
    """Отправляем запрос к API с контекстом диалога"""
    chat_response = client.chat(model=model, messages=chat_context[chat_id])
    user = update.effective_user
    logger.info(f"Пользователь {user.id} {user.first_name} отправил сообщение: {user_message}")
    """Добавляем ответ модели к контексту диалога"""
    chat_context[chat_id].append(ChatMessage(role="assistant", content=chat_response.choices[0].message.content))

    await context.bot.send_message(chat_id=chat_id, text=chat_response.choices[0].message.content)
    logger.info(f"Бот ответил пользователю {user.id} {user.first_name} : {chat_response.choices[0].message.content}")

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    """application.add_handler(CommandHandler("tokens", tokens))"""
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == '__main__':
    main()

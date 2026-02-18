import logging
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import database as db
import config

# Состояния для диалога создания заявки
PRODUCT_SELECT, QUANTITY_INPUT = range(2)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = [
        [KeyboardButton("Список товаров")],
        [KeyboardButton("Создать заявку")],
        [KeyboardButton("Статус заявок")],
        [KeyboardButton("Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n\n"
        "Я бот для управления складскими заявками. Я помогу вам:\n"
        "• Просматривать список доступных товаров\n"
        "• Создавать заявки на отгрузку\n"
        "• Отслеживать статус заявок\n\n"
        "Выберите действие на клавиатуре ниже:",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Доступные команды:\n\n"
        "/start - начать работу с ботом\n"
        "/products - список товаров\n"
        "/order - создать заявку\n"
        "/status - статус заявок\n"
        "/dashboard - ссылка на дашборд\n"
        "/help - показать помощь"
    )


async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список товаров"""
    products_list = db.get_products()
    if not products_list:
        await update.message.reply_text("Товары не найдены")
        return

    message = "Доступные товары:\n\n"
    for p in products_list:
        message += f"🔹 {p[1]}\n"
        message += f"   Категория: {p[2]}\n"
        message += f"   В наличии: {p[3]} шт.\n"
        message += f"   Цена: {p[4]} руб.\n\n"

    await update.message.reply_text(message)


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс создания заявки"""
    products_list = db.get_products()
    if not products_list:
        await update.message.reply_text("Нет доступных товаров")
        return ConversationHandler.END

    # Создаем клавиатуру с товарами
    keyboard = []
    for p in products_list:
        keyboard.append([KeyboardButton(f"{p[1]} (ID: {p[0]})")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Выберите товар из списка:",
        reply_markup=reply_markup
    )
    return PRODUCT_SELECT


async def product_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора товара"""
    text = update.message.text

    # Извлекаем ID товара из текста кнопки
    match = re.search(r'ID: (\d+)', text)
    if match:
        product_id = int(match.group(1))
        context.user_data['product_id'] = product_id
        await update.message.reply_text(
            "Введите количество:",
            reply_markup=get_main_keyboard()
        )
        return QUANTITY_INPUT
    else:
        await update.message.reply_text("Не удалось определить товар. Попробуйте снова.")
        return ConversationHandler.END


async def quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода количества"""
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            await update.message.reply_text("Количество должно быть положительным числом. Попробуйте снова:")
            return QUANTITY_INPUT

        # Получаем данные из контекста
        user = update.effective_user
        product_id = context.user_data.get('product_id')

        if not product_id:
            await update.message.reply_text("Ошибка: не выбран товар. Начните заново.")
            return ConversationHandler.END

        # Создаем заявку
        success, message = db.create_order(
            user.id,
            user.full_name or user.username or str(user.id),
            product_id,
            quantity
        )

        await update.message.reply_text(
            message,
            reply_markup=get_main_keyboard()
        )

        # Очищаем данные
        context.user_data.clear()
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return QUANTITY_INPUT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статус заявок пользователя"""
    user = update.effective_user
    orders = db.get_order_status(user.id)

    if not orders:
        await update.message.reply_text("У вас нет заявок")
        return

    message = "Ваши заявки:\n\n"
    for o in orders:
        message += f"   Заявка №{o[0]}\n"
        message += f"   Товар: {o[1]}\n"
        message += f"   Количество: {o[2]} шт.\n"
        message += f"   Статус: {o[3]}\n"
        message += f"   Дата: {o[4]}\n\n"

    await update.message.reply_text(message)


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить ссылку на дашборд"""
    await update.message.reply_text(
        'Дашборд доступен по адресу: http://127.0.0.1:8050\n'
        'Для работы дашборда необходимо запустить файл dashboard.py отдельно.'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (кнопок)"""
    text = update.message.text

    if text == "Список товаров":
        await products(update, context)
    elif text == "Создать заявку":
        await order_start(update, context)
    elif text == "Статус заявок":
        await status(update, context)
    elif text == "Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки на клавиатуре или команды /help",
            reply_markup=get_main_keyboard()
        )


def main():
    """Главная функция запуска бота"""
    # Инициализация базы данных
    db.init_db()

    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Обработчик диалога создания заявки
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('order', order_start),
            MessageHandler(filters.Text('Создать заявку'), order_start)
        ],
        states={
            PRODUCT_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_select)],
            QUANTITY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_input)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Добавление обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('products', products))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('dashboard', dashboard))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот @Warehouse2026Bot запущен")
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()


if __name__ == '__main__':
    main()
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменной окружения
TOKEN = os.getenv("TOKEN", "8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA")

# Тарифы
PLANS = {
    "basic": {
        "name": "Базовый", 
        "price": 99, 
        "duration": "1 месяц", 
        "features": ["1 подключение", "10+ стран", "Базовая поддержка"],
        "yoomoney": "https://yoomoney.ru/to/4100118775331265?sum=99"
    },
    "premium": {
        "name": "Премиум", 
        "price": 199, 
        "duration": "1 месяц", 
        "features": ["5 подключений", "10+ стран", "Приоритетная поддержка", "Без логирования"],
        "yoomoney": "https://yoomoney.ru/to/4100118775331265?sum=199"
    },
    "yearly": {
        "name": "Годовой", 
        "price": 240, 
        "duration": "1 месяц", 
        "features": ["5 подключений", "10+ стран", "24/7 поддержка", "Без логирования"],
        "yoomoney": "https://yoomoney.ru/to/4100118775331265?sum=240"
    }
}

# Ссылка на Юмани кошелек
YOOMONEY_WALLET = "https://yoomoney.ru/to/4100118775331265"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
🔒 Добро пожаловать в MorphVPN! 🔒

Привет, {user.first_name}! 👋

Мы предлагаем быстрый, надежный и безопасный VPN сервис для всех устройств.

✨ Наши преимущества:
• 256-битное шифрование
• Серверы в 10+ странах
• Без логирования
• Поддержка всех устройств
• 30-дневная гарантия возврата

Выбери тариф ниже или узнай больше информации:
"""
    
    keyboard = [
        [InlineKeyboardButton("💰 Выбрать тариф", callback_data="show_plans")],
        [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about"),
         InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("📞 Поддержка", url="https://t.me/slogg12")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показываем доступные тарифы"""
    query = update.callback_query
    await query.answer()
    
    text = "📦 Выбери подходящий тариф:\n\n"
    
    keyboard = []
    for plan_id, plan in PLANS.items():
        button_text = f"{plan['name']} - {plan['price']}₽/{plan['duration']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_{plan_id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора тарифа"""
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    
    if plan_id not in PLANS:
        await query.answer("Ошибка: тариф не найден")
        return
    
    plan = PLANS[plan_id]
    
    features_text = "\n".join([f"✓ {feature}" for feature in plan['features']])
    
    text = f"""
💎 {plan['name']} тариф

💰 Цена: {plan['price']}₽ за {plan['duration']}

📋 Включено:
{features_text}

✅ 30-дневная гарантия возврата денег
✅ Без логирования
✅ 24/7 поддержка
"""
    
    keyboard = [
        [InlineKeyboardButton("✅ Купить", callback_data=f"buy_{plan_id}")],
        [InlineKeyboardButton("◀️ Другие тарифы", callback_data="show_plans")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик покупки"""
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    
    if plan_id not in PLANS:
        await query.answer("Ошибка: тариф не найден")
        return
    
    plan = PLANS[plan_id]
    user = query.from_user
    
    text = f"""
✅ Спасибо за выбор!

Вы выбрали: {plan['name']} ({plan['price']}₽)

📝 Для завершения покупки:

1️⃣ Нажми кнопку "💳 Оплатить {plan['price']}₽"
2️⃣ Выполни платеж в Юмани
3️⃣ Нажми "✅ Я оплатил"
4️⃣ Получи доступ сразу после оплаты

❓ Возникли вопросы?
Напиши нам в поддержку: @slogg12

Спасибо, что выбрал MorphVPN! 🙏
"""
    
    keyboard = [
        [InlineKeyboardButton(f"💳 Оплатить {plan['price']}₽", url=plan['yoomoney'])],
        [InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_{plan_id}")],
        [InlineKeyboardButton("📞 Поддержка", url="https://t.me/slogg12")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    # Логируем покупку
    logger.info(f"User {user.id} ({user.first_name}) selected plan: {plan_id}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Информация о сервисе"""
    query = update.callback_query
    await query.answer()
    
    text = """
ℹ️ О MorphVPN

MorphVPN - это современный VPN сервис, который обеспечивает:

🔒 Безопасность:
• 256-битное военное шифрование
• Без логирования активности
• Защита от утечек DNS/IP

⚡ Производительность:
• Серверы по всему миру
• Высокая скорость соединения
• Минимальная задержка

📱 Совместимость:
• Windows, Mac, iOS, Android
• Linux поддержка
• 5 одновременных подключений

💰 Доступность:
• Низкие цены
• 30-дневная гарантия возврата
• Гибкие тарифы

🌍 Серверы в 10+ странах

Присоединяйся к тысячам довольных пользователей!
"""
    
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """FAQ"""
    query = update.callback_query
    await query.answer()
    
    text = """
❓ Часто задаваемые вопросы

❓ Что такое VPN?
VPN (Virtual Private Network) - это сервис, который шифрует ваше соединение и скрывает IP-адрес.

❓ Законно ли использовать VPN?
Да, использование VPN полностью законно в большинстве стран.

❓ Замедлит ли VPN мой интернет?
Небольшое замедление возможно, но наши серверы оптимизированы для минимального влияния.

❓ Какие устройства поддерживаются?
Windows, Mac, iOS, Android и Linux.

❓ Есть ли бесплатный пробный период?
Да, 7 дней бесплатно без указания данных карты.

❓ Как отменить подписку?
Отмени в личном кабинете. Возврат в течение 30 дней.

❓ Вы сохраняете мои данные?
Нет! Мы придерживаемся строгой политики отсутствия логирования.

Еще вопросы? Напиши в поддержку: @slogg12
"""
    
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    text = """
🔒 MorphVPN 🔒

Быстрый, надежный и безопасный VPN сервис для всех устройств.

Выбери действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("💰 Выбрать тариф", callback_data="show_plans")],
        [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about"),
         InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("📞 Поддержка", url="https://t.me/slogg12")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    help_text = """
📖 Доступные команды:

/start - Начать работу с ботом
/help - Показать эту справку
/plans - Показать тарифы
/about - Информация о сервисе
/faq - Часто задаваемые вопросы
/support - Связаться с поддержкой

Или используй кнопки ниже! 👇
"""
    await update.message.reply_text(help_text)

async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /plans"""
    text = "📦 Наши тарифы:\n\n"
    
    for plan_id, plan in PLANS.items():
        features = ", ".join(plan['features'])
        text += f"💎 {plan['name']}: {plan['price']}₽\n{features}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("💰 Выбрать тариф", callback_data="show_plans")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    text = """
🔒 MorphVPN 🔒

Быстрый, надежный и безопасный VPN сервис для всех устройств.

Выбери действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("💰 Выбрать тариф", callback_data="show_plans")],
        [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about"),
         InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("📞 Поддержка", url="https://t.me/slogg12")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def paid_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Я оплатил'"""
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    
    if plan_id not in PLANS:
        await query.answer("Ошибка: тариф не найден")
        return
    
    plan = PLANS[plan_id]
    user = query.from_user
    
    text = f"""
✅ Спасибо за оплату!

Вы оплатили: {plan['name']} ({plan['price']}₽)

📋 Ваш тариф активирован!

Включено:
"""
    
    for feature in plan['features']:
        text += f"\n✓ {feature}"
    
    text += f"""

🔑 Для получения конфига:

Напиши мне в Telegram: @slogg12

Укажи:
• Свой ID: {user.id}
• Выбранный тариф: {plan['name']}
• Устройство: (Windows/Mac/iOS/Android/Linux)

Я отправлю тебе конфиг в течение 5 минут! ⚡

Спасибо за выбор MorphVPN! 🙏
"""
    
    keyboard = [
        [InlineKeyboardButton("📞 Написать в поддержку", url="https://t.me/slogg12")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    # Логируем оплату
    logger.info(f"User {user.id} ({user.first_name}) paid for plan: {plan_id}")

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("plans", plans_command))

    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(show_plans, pattern="^show_plans$"))
    application.add_handler(CallbackQueryHandler(select_plan, pattern="^select_"))
    application.add_handler(CallbackQueryHandler(buy_plan, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(paid_plan, pattern="^paid_"))
    application.add_handler(CallbackQueryHandler(about, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(faq, pattern="^faq$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))

    # Запускаем бота
    print("🤖 Бот MorphVPN запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()

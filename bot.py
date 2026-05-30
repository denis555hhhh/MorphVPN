import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("TOKEN", "8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA")

# URL базы данных PostgreSQL (Railway автоматически добавляет DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")

# QR код СБП для оплаты
QR_FILE_ID = "AgACAgIAAxkBAAFLCEFqGrtrg4MB1kNbedVTpwawTFWYhgACfRxrG76y0UjuwekbsyxkGQEAAwIAA20AAzsE"
PLANS = {
    "basic": {
        "name": "Базовый",
        "price": 99,
        "duration": "1 месяц",
        "features": ["1 подключение", "10+ стран", "Базовая поддержка"],
        "yoomoney": "https://yoomoney.ru/to/4100118775331265/99"
    },
    "premium": {
        "name": "Премиум",
        "price": 199,
        "duration": "1 месяц",
        "features": ["5 подключений", "10+ стран", "Приоритетная поддержка", "Без логирования"],
        "yoomoney": "https://yoomoney.ru/to/4100118775331265/199"
    },
    "yearly": {
        "name": "Годовой",
        "price": 240,
        "duration": "1 месяц",
        "features": ["5 подключений", "10+ стран", "24/7 поддержка", "Без логирования"],
        "yoomoney": "https://yoomoney.ru/to/4100118775331265/240"
    }
}

# ─────────────────────────────────────────────
# БАЗА ДАННЫХ
# ─────────────────────────────────────────────

def get_db():
    """Подключение к PostgreSQL"""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL не задан — работаем без БД")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return None

def init_db():
    """Создаём таблицы при первом запуске"""
    conn = get_db()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            # Таблица пользователей
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     BIGINT PRIMARY KEY,
                    username    TEXT,
                    first_name  TEXT,
                    joined_at   TIMESTAMP DEFAULT NOW()
                )
            """)
            # Таблица заказов
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id          SERIAL PRIMARY KEY,
                    user_id     BIGINT REFERENCES users(user_id),
                    plan_id     TEXT NOT NULL,
                    plan_name   TEXT NOT NULL,
                    price       INTEGER NOT NULL,
                    status      TEXT DEFAULT 'pending',
                    created_at  TIMESTAMP DEFAULT NOW()
                )
            """)
            # Таблица активных подписок
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id          SERIAL PRIMARY KEY,
                    user_id     BIGINT REFERENCES users(user_id),
                    plan_id     TEXT NOT NULL,
                    plan_name   TEXT NOT NULL,
                    activated_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
    finally:
        conn.close()

def save_user(user_id: int, username: str, first_name: str):
    """Сохраняем/обновляем пользователя"""
    conn = get_db()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, username, first_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
            """, (user_id, username, first_name))
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    finally:
        conn.close()

def save_order(user_id: int, plan_id: str, plan_name: str, price: int):
    """Сохраняем заказ"""
    conn = get_db()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders (user_id, plan_id, plan_name, price, status)
                VALUES (%s, %s, %s, %s, 'pending')
            """, (user_id, plan_id, plan_name, price))
        conn.commit()
        logger.info(f"Заказ сохранён: user={user_id}, plan={plan_id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения заказа: {e}")
    finally:
        conn.close()

def confirm_payment(user_id: int, plan_id: str, plan_name: str):
    """Подтверждаем оплату и создаём подписку"""
    conn = get_db()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            # Обновляем статус последнего заказа
            cur.execute("""
                UPDATE orders SET status = 'paid'
                WHERE user_id = %s AND plan_id = %s AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, plan_id))
            # Создаём подписку
            cur.execute("""
                INSERT INTO subscriptions (user_id, plan_id, plan_name)
                VALUES (%s, %s, %s)
            """, (user_id, plan_id, plan_name))
        conn.commit()
        logger.info(f"Оплата подтверждена: user={user_id}, plan={plan_id}")
    except Exception as e:
        logger.error(f"Ошибка подтверждения оплаты: {e}")
    finally:
        conn.close()

def get_user_stats():
    """Статистика для админа"""
    conn = get_db()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM users")
            users = cur.fetchone()
            cur.execute("SELECT COUNT(*) as total FROM orders WHERE status = 'paid'")
            paid = cur.fetchone()
            cur.execute("SELECT SUM(price) as total FROM orders WHERE status = 'paid'")
            revenue = cur.fetchone()
        return {
            "users": users["total"],
            "paid_orders": paid["total"],
            "revenue": revenue["total"] or 0
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return None
    finally:
        conn.close()

# ─────────────────────────────────────────────
# ОБРАБОТЧИКИ БОТА
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # Сохраняем пользователя в БД
    save_user(user.id, user.username or "", user.first_name)

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
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    text = "📦 Выбери подходящий тариф:\n\n"
    keyboard = []
    for plan_id, plan in PLANS.items():
        keyboard.append([InlineKeyboardButton(
            f"{plan['name']} — {plan['price']}₽/{plan['duration']}",
            callback_data=f"select_{plan_id}"
        )])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    if plan_id not in PLANS:
        await query.answer("Ошибка: тариф не найден")
        return

    plan = PLANS[plan_id]
    features_text = "\n".join([f"✓ {f}" for f in plan['features']])
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
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    if plan_id not in PLANS:
        await query.answer("Ошибка: тариф не найден")
        return

    plan = PLANS[plan_id]
    user = query.from_user

    # Сохраняем заказ в БД
    save_order(user.id, plan_id, plan['name'], plan['price'])

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
"""
    keyboard = [
        [InlineKeyboardButton(f"💳 Оплатить {plan['price']}₽", url=plan['yoomoney'])],
        [InlineKeyboardButton("📱 Оплатить через QR (СБП)", callback_data=f"qr_{plan_id}")],
        [InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_{plan_id}")],
        [InlineKeyboardButton("📞 Поддержка", url="https://t.me/slogg12")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    logger.info(f"User {user.id} ({user.first_name}) selected plan: {plan_id}")


async def show_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    plan = PLANS.get(plan_id, {})
    price = plan.get('price', '')
    await query.answer()
    await query.message.reply_photo(
        photo=QR_FILE_ID,
        caption=(
            f"📱 *QR код для оплаты через СБП*\n\n"
            f"💰 Сумма к оплате: *{price}₽*\n\n"
            f"1️⃣ Отсканируй QR камерой телефона\n"
            f"2️⃣ Введи сумму *{price}* рублей\n"
            f"3️⃣ Подтверди платёж\n"
            f"4️⃣ Нажми кнопку ✅ Я оплатил в боте\n\n"
            f"❓ Вопросы? @slogg12"
        ),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_{plan_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"buy_{plan_id}")]
        ])
    )


async def paid_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    plan_id = query.data.split("_")[1]
    if plan_id not in PLANS:
        await query.answer("Ошибка: тариф не найден")
        return

    plan = PLANS[plan_id]
    user = query.from_user

    # Подтверждаем оплату в БД
    confirm_payment(user.id, plan_id, plan['name'])

    text = f"""
✅ Спасибо за оплату!

Вы оплатили: {plan['name']} ({plan['price']}₽)

📋 Ваш тариф активирован!

Включено:
"""
    for feature in plan['features']:
        text += f"\n✓ {feature}"

    text += f"""

🔑 Для получения конфига напиши: @slogg12

Укажи:
• Свой ID: {user.id}
• Тариф: {plan['name']}
• Устройство: (Windows/Mac/iOS/Android/Linux)

Конфиг придёт в течение 5 минут! ⚡

Спасибо за выбор MorphVPN! 🙏
"""
    keyboard = [
        [InlineKeyboardButton("📞 Написать в поддержку", url="https://t.me/slogg12")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu")]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    logger.info(f"User {user.id} ({user.first_name}) paid for plan: {plan_id}")


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    text = """
ℹ️ О MorphVPN

MorphVPN — современный VPN сервис:

🔒 Безопасность:
• 256-битное военное шифрование
• Без логирования активности
• Защита от утечек DNS/IP

⚡ Производительность:
• Серверы по всему миру
• Высокая скорость соединения

📱 Совместимость:
• Windows, Mac, iOS, Android, Linux
• 5 одновременных подключений

💰 Доступность:
• Низкие цены
• 30-дневная гарантия возврата

🌍 Серверы в 10+ странах
"""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    text = """
❓ Часто задаваемые вопросы

❓ Что такое VPN?
Сервис, который шифрует соединение и скрывает IP-адрес.

❓ Законно ли использовать VPN?
Да, в большинстве стран это законно.

❓ Замедлит ли VPN интернет?
Минимально — серверы оптимизированы.

❓ Какие устройства поддерживаются?
Windows, Mac, iOS, Android, Linux.

❓ Есть ли пробный период?
Да, 7 дней бесплатно.

❓ Вы сохраняете мои данные?
Нет! Строгая политика без логирования.

Вопросы? Напиши: @slogg12
"""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
📖 Доступные команды:

/start — Начать работу с ботом
/help — Показать справку
/plans — Показать тарифы
/stats — Статистика (только для админа)

Или используй кнопки! 👇
"""
    await update.message.reply_text(help_text)


async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "📦 Наши тарифы:\n\n"
    for plan_id, plan in PLANS.items():
        features = ", ".join(plan['features'])
        text += f"💎 {plan['name']}: {plan['price']}₽\n{features}\n\n"
    keyboard = [[InlineKeyboardButton("💰 Выбрать тариф", callback_data="show_plans")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Статистика для админа"""
    stats = get_user_stats()
    if not stats:
        await update.message.reply_text("❌ База данных недоступна")
        return
    text = f"""
📊 Статистика MorphVPN

👥 Пользователей: {stats['users']}
✅ Оплаченных заказов: {stats['paid_orders']}
💰 Выручка: {stats['revenue']}₽
"""
    await update.message.reply_text(text)


# ─────────────────────────────────────────────
# ЗАПУСК
# ─────────────────────────────────────────────

def main() -> None:
    # Инициализируем БД
    init_db()

    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("plans", plans_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Кнопки
    application.add_handler(CallbackQueryHandler(show_plans, pattern="^show_plans$"))
    application.add_handler(CallbackQueryHandler(select_plan, pattern="^select_"))
    application.add_handler(CallbackQueryHandler(buy_plan, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(show_qr, pattern="^qr_"))
    application.add_handler(CallbackQueryHandler(paid_plan, pattern="^paid_"))
    application.add_handler(CallbackQueryHandler(about, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(faq, pattern="^faq$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))

    print("🤖 Бот MorphVPN запущен!")
    application.run_polling()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import threading
import time

# ─── Цвета для консоли ───────────────────────────────────────────────────────
try:
    import colorama
    colorama.init()
    R  = "\033[91m"   # красный
    G  = "\033[92m"   # зелёный
    Y  = "\033[93m"   # жёлтый
    B  = "\033[94m"   # синий
    M  = "\033[95m"   # фиолетовый
    C  = "\033[96m"   # голубой
    W  = "\033[97m"   # белый
    DIM = "\033[2m"
    RST = "\033[0m"
except ImportError:
    R=G=Y=B=M=C=W=DIM=RST=""

# ─── Настройки ────────────────────────────────────────────────────────────────
TOKEN       = os.getenv("TOKEN", "8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA")
DATABASE_URL = os.getenv("DATABASE_URL", "")
BOT_SCRIPT  = os.path.join(os.path.dirname(__file__), "bot.py")

bot_process = None

# ─── Утилиты ──────────────────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input(f"\n{DIM}  Нажми Enter чтобы продолжить...{RST}")

def header():
    print(f"""
{C}╔══════════════════════════════════════════════════════╗
║          {W}🔒  MorphVPN  —  Панель администратора{C}        ║
╚══════════════════════════════════════════════════════╝{RST}""")

def status_line():
    global bot_process
    if bot_process and bot_process.poll() is None:
        st = f"{G}● БОТ ЗАПУЩЕН  (PID {bot_process.pid}){RST}"
    else:
        st = f"{R}○ БОТ ОСТАНОВЛЕН{RST}"

    db_ok = "✓ БД подключена" if DATABASE_URL else "✗ DATABASE_URL не задан"
    db_col = G if DATABASE_URL else Y
    print(f"  Статус: {st}   {db_col}{db_ok}{RST}\n")

# ─── БД ───────────────────────────────────────────────────────────────────────
def get_db():
    if not DATABASE_URL:
        print(f"{Y}  ⚠  DATABASE_URL не задан. Введи его в .env или переменные окружения.{RST}")
        return None
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"{R}  ✗ Ошибка подключения к БД: {e}{RST}")
        return None

# ─── МЕНЮ ─────────────────────────────────────────────────────────────────────
def main_menu():
    clear()
    header()
    status_line()
    print(f"""  {W}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RST}
  {G}[1]{RST} 🚀  Запустить бота
  {R}[2]{RST} ⛔  Остановить бота
  {Y}[3]{RST} 🔄  Перезапустить бота
  {C}[4]{RST} 📊  Статистика (БД)
  {B}[5]{RST} 👥  Список пользователей
  {M}[6]{RST} 📦  Список заказов
  {W}[7]{RST} ✅  Подтверждённые оплаты
  {C}[8]{RST} 🔍  Найти пользователя
  {Y}[9]{RST} 🗑   Очистить pending-заказы
  {G}[10]{RST} 📋  Просмотр логов бота
  {R}[0]{RST} ❌  Выход
  {W}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RST}""")
    return input(f"\n  {C}Выбери пункт:{RST} ").strip()

# ─── 1. Запуск бота ───────────────────────────────────────────────────────────
def start_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        print(f"{Y}  ⚠  Бот уже запущен (PID {bot_process.pid}){RST}")
        pause(); return
    env = os.environ.copy()
    env["TOKEN"] = TOKEN
    if DATABASE_URL:
        env["DATABASE_URL"] = DATABASE_URL
    bot_process = subprocess.Popen(
        [sys.executable, BOT_SCRIPT],
        env=env,
        stdout=open("bot.log", "a", encoding="utf-8"),
        stderr=subprocess.STDOUT
    )
    time.sleep(1)
    if bot_process.poll() is None:
        print(f"{G}  ✓ Бот запущен! PID: {bot_process.pid}{RST}")
    else:
        print(f"{R}  ✗ Бот не запустился. Проверь bot.log{RST}")
    pause()

# ─── 2. Остановка бота ────────────────────────────────────────────────────────
def stop_bot():
    global bot_process
    if not bot_process or bot_process.poll() is not None:
        print(f"{Y}  ⚠  Бот не запущен{RST}")
        pause(); return
    bot_process.terminate()
    bot_process.wait(timeout=5)
    print(f"{G}  ✓ Бот остановлен{RST}")
    pause()

# ─── 3. Перезапуск ────────────────────────────────────────────────────────────
def restart_bot():
    stop_bot()
    time.sleep(1)
    start_bot()

# ─── 4. Статистика ────────────────────────────────────────────────────────────
def show_stats():
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as c FROM users")
            users = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders")
            orders_total = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='paid'")
            orders_paid = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'")
            orders_pend = cur.fetchone()["c"]
            cur.execute("SELECT COALESCE(SUM(price),0) as s FROM orders WHERE status='paid'")
            revenue = cur.fetchone()["s"]
            cur.execute("SELECT COUNT(*) as c FROM subscriptions")
            subs = cur.fetchone()["c"]
        print(f"""
{C}  ┌─────────────────────────────────────┐
  │        📊  СТАТИСТИКА MorphVPN       │
  ├─────────────────────────────────────┤{RST}
  {W}  👥 Пользователей:{RST}        {G}{users}{RST}
  {W}  📦 Всего заказов:{RST}        {Y}{orders_total}{RST}
  {W}  ✅ Оплачено:{RST}             {G}{orders_paid}{RST}
  {W}  ⏳ Ожидают оплаты:{RST}       {Y}{orders_pend}{RST}
  {W}  🔑 Активных подписок:{RST}    {G}{subs}{RST}
  {W}  💰 Выручка:{RST}              {G}{revenue} ₽{RST}
{C}  └─────────────────────────────────────┘{RST}""")
    except Exception as e:
        print(f"{R}  ✗ Ошибка: {e}{RST}")
    finally:
        conn.close()
    pause()

# ─── 5. Список пользователей ──────────────────────────────────────────────────
def show_users():
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, username, first_name, joined_at FROM users ORDER BY joined_at DESC LIMIT 50")
            rows = cur.fetchall()
        if not rows:
            print(f"{Y}  Пользователей нет{RST}")
        else:
            print(f"\n{C}  {'ID':<14} {'Username':<20} {'Имя':<20} {'Дата'}{RST}")
            print(f"  {'─'*70}")
            for r in rows:
                uname = f"@{r['username']}" if r['username'] else "—"
                dt = str(r['joined_at'])[:16]
                print(f"  {W}{r['user_id']:<14}{RST} {uname:<20} {r['first_name']:<20} {DIM}{dt}{RST}")
        print(f"\n{DIM}  Показаны последние 50{RST}")
    except Exception as e:
        print(f"{R}  ✗ Ошибка: {e}{RST}")
    finally:
        conn.close()
    pause()

# ─── 6. Список заказов ────────────────────────────────────────────────────────
def show_orders():
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, o.user_id, u.first_name, o.plan_name, o.price, o.status, o.created_at
                FROM orders o LEFT JOIN users u ON o.user_id=u.user_id
                ORDER BY o.created_at DESC LIMIT 50
            """)
            rows = cur.fetchall()
        if not rows:
            print(f"{Y}  Заказов нет{RST}")
        else:
            print(f"\n{C}  {'#':<5} {'UserID':<13} {'Имя':<16} {'Тариф':<12} {'Цена':<8} {'Статус':<10} {'Дата'}{RST}")
            print(f"  {'─'*80}")
            for r in rows:
                st_col = G if r['status'] == 'paid' else Y
                dt = str(r['created_at'])[:16]
                print(f"  {r['id']:<5} {W}{r['user_id']:<13}{RST} {(r['first_name'] or '—'):<16} {r['plan_name']:<12} {r['price']:<8} {st_col}{r['status']:<10}{RST} {DIM}{dt}{RST}")
        print(f"\n{DIM}  Показаны последние 50{RST}")
    except Exception as e:
        print(f"{R}  ✗ Ошибка: {e}{RST}")
    finally:
        conn.close()
    pause()

# ─── 7. Подтверждённые оплаты ─────────────────────────────────────────────────
def show_paid():
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.id, s.user_id, u.first_name, u.username, s.plan_name, s.activated_at
                FROM subscriptions s LEFT JOIN users u ON s.user_id=u.user_id
                ORDER BY s.activated_at DESC LIMIT 50
            """)
            rows = cur.fetchall()
        if not rows:
            print(f"{Y}  Оплат нет{RST}")
        else:
            print(f"\n{C}  {'#':<5} {'UserID':<13} {'Имя':<16} {'Username':<18} {'Тариф':<12} {'Дата'}{RST}")
            print(f"  {'─'*80}")
            for r in rows:
                uname = f"@{r['username']}" if r['username'] else "—"
                dt = str(r['activated_at'])[:16]
                print(f"  {G}{r['id']:<5}{RST} {W}{r['user_id']:<13}{RST} {(r['first_name'] or '—'):<16} {uname:<18} {r['plan_name']:<12} {DIM}{dt}{RST}")
    except Exception as e:
        print(f"{R}  ✗ Ошибка: {e}{RST}")
    finally:
        conn.close()
    pause()

# ─── 8. Поиск пользователя ────────────────────────────────────────────────────
def search_user():
    query_str = input(f"\n  {C}Введи ID или username:{RST} ").strip()
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            if query_str.isdigit():
                cur.execute("SELECT * FROM users WHERE user_id=%s", (int(query_str),))
            else:
                uname = query_str.lstrip("@")
                cur.execute("SELECT * FROM users WHERE username ILIKE %s", (f"%{uname}%",))
            user = cur.fetchone()
            if not user:
                print(f"{Y}  Пользователь не найден{RST}")
                pause(); return
            print(f"""
{C}  ┌─────────────────────────────────────┐
  │         👤  ПОЛЬЗОВАТЕЛЬ             │
  ├─────────────────────────────────────┤{RST}
  {W}  ID:{RST}          {G}{user['user_id']}{RST}
  {W}  Имя:{RST}         {user['first_name']}
  {W}  Username:{RST}    @{user['username'] or '—'}
  {W}  Регистрация:{RST} {str(user['joined_at'])[:16]}""")
            # Заказы пользователя
            cur.execute("SELECT plan_name, price, status, created_at FROM orders WHERE user_id=%s ORDER BY created_at DESC", (user['user_id'],))
            orders = cur.fetchall()
            if orders:
                print(f"\n{C}  Заказы:{RST}")
                for o in orders:
                    st_col = G if o['status'] == 'paid' else Y
                    print(f"    {o['plan_name']} — {o['price']}₽ — {st_col}{o['status']}{RST} — {DIM}{str(o['created_at'])[:16]}{RST}")
            else:
                print(f"\n  {DIM}Заказов нет{RST}")
            print(f"{C}  └─────────────────────────────────────┘{RST}")
    except Exception as e:
        print(f"{R}  ✗ Ошибка: {e}{RST}")
    finally:
        conn.close()
    pause()

# ─── 9. Очистить pending ──────────────────────────────────────────────────────
def clear_pending():
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'")
            cnt = cur.fetchone()["c"]
        if cnt == 0:
            print(f"{G}  Нет pending-заказов{RST}")
            pause(); return
        confirm = input(f"{Y}  Удалить {cnt} pending-заказов? (да/нет):{RST} ").strip().lower()
        if confirm in ("да", "y", "yes"):
            with conn.cursor() as cur:
                cur.execute("DELETE FROM orders WHERE status='pending'")
            conn.commit()
            print(f"{G}  ✓ Удалено {cnt} заказов{RST}")
        else:
            print(f"{DIM}  Отменено{RST}")
    except Exception as e:
        print(f"{R}  ✗ Ошибка: {e}{RST}")
    finally:
        conn.close()
    pause()

# ─── 10. Логи бота ────────────────────────────────────────────────────────────
def show_logs():
    log_file = os.path.join(os.path.dirname(__file__), "bot.log")
    if not os.path.exists(log_file):
        print(f"{Y}  Файл bot.log не найден. Запусти бота сначала.{RST}")
        pause(); return
    print(f"\n{C}  ─── Последние 40 строк bot.log ───{RST}\n")
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for line in lines[-40:]:
        line = line.rstrip()
        if "ERROR" in line:
            print(f"  {R}{line}{RST}")
        elif "WARNING" in line:
            print(f"  {Y}{line}{RST}")
        elif "INFO" in line:
            print(f"  {DIM}{line}{RST}")
        else:
            print(f"  {line}")
    pause()

# ─── ГЛАВНЫЙ ЦИКЛ ─────────────────────────────────────────────────────────────
def run():
    # Установка зависимостей если нужно
    try:
        import psycopg2
        import colorama
    except ImportError:
        print("Устанавливаю зависимости...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary", "colorama", "-q"])
        import colorama
        colorama.init()

    while True:
        choice = main_menu()
        if   choice == "1":  start_bot()
        elif choice == "2":  stop_bot()
        elif choice == "3":  restart_bot()
        elif choice == "4":  show_stats()
        elif choice == "5":  show_users()
        elif choice == "6":  show_orders()
        elif choice == "7":  show_paid()
        elif choice == "8":  search_user()
        elif choice == "9":  clear_pending()
        elif choice == "10": show_logs()
        elif choice == "0":
            stop_bot()
            print(f"\n{G}  До свидания!{RST}\n")
            sys.exit(0)
        else:
            print(f"{R}  Неверный выбор{RST}")
            time.sleep(0.8)

if __name__ == "__main__":
    run()

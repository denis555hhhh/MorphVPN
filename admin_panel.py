# -*- coding: utf-8 -*-
"""
MorphVPN Launcher — Полноценная панель управления ботом
"""
import os, sys, subprocess, time, threading, shutil

# ── Авто-установка зависимостей ──────────────────────────────────────────────
def _install(pkg):
    subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=False)

try:
    import colorama; colorama.init(autoreset=True)
except ImportError:
    _install("colorama"); import colorama; colorama.init(autoreset=True)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    _install("psycopg2-binary")
    import psycopg2
    from psycopg2.extras import RealDictCursor

# ── Цвета ────────────────────────────────────────────────────────────────────
R   = "\033[91m"
G   = "\033[92m"
Y   = "\033[93m"
B   = "\033[94m"
M   = "\033[95m"
C   = "\033[96m"
W   = "\033[97m"
DIM = "\033[2m"
BLD = "\033[1m"
RST = "\033[0m"

# ── Пути и конфиг ─────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.abspath(__file__))
BOT_SCRIPT  = os.path.join(BASE, "bot.py")
ENV_FILE    = os.path.join(BASE, ".env")
LOG_FILE    = os.path.join(BASE, "bot.log")

TOKEN        = os.getenv("TOKEN", "8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA")
DATABASE_URL = os.getenv("DATABASE_URL", "")

bot_process: subprocess.Popen = None

# ── .env ─────────────────────────────────────────────────────────────────────
def load_env():
    global TOKEN, DATABASE_URL
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip(); v = v.strip().strip('"').strip("'")
            if k == "TOKEN" and v:
                TOKEN = v; os.environ["TOKEN"] = v
            if k == "DATABASE_URL" and v:
                DATABASE_URL = v; os.environ["DATABASE_URL"] = v

def save_env():
    with open(ENV_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"TOKEN={TOKEN}\n")
        f.write(f"DATABASE_URL={DATABASE_URL}\n")

# ── Утилиты ───────────────────────────────────────────────────────────────────
def cls():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg="  Нажми Enter чтобы продолжить..."):
    input(f"\n{DIM}{msg}{RST}")

def term_width():
    return shutil.get_terminal_size((80, 24)).columns

def divider(ch="─", col=C):
    w = min(term_width() - 4, 70)
    print(f"  {col}{ch * w}{RST}")

def bot_running():
    return bot_process is not None and bot_process.poll() is None

# ── Анимация загрузки ─────────────────────────────────────────────────────────
def loading(msg, seconds=1.5):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    end = time.time() + seconds
    i = 0
    while time.time() < end:
        print(f"\r  {C}{frames[i % len(frames)]}{RST}  {msg}", end="", flush=True)
        time.sleep(0.1); i += 1
    print(f"\r  {G}✓{RST}  {msg}{'  ':10}")

# ── Шапка ─────────────────────────────────────────────────────────────────────
def header():
    cls()
    print(f"""
{C}{BLD}  ╔══════════════════════════════════════════════════════════╗
  ║   {W}🔒  MorphVPN  ·  Панель управления  ·  v2.0{C}            ║
  ╚══════════════════════════════════════════════════════════╝{RST}""")

def status_bar():
    # Бот
    if bot_running():
        bot_st = f"{G}{BLD}● ЗАПУЩЕН{RST}  {DIM}PID {bot_process.pid}{RST}"
    else:
        bot_st = f"{R}○ ОСТАНОВЛЕН{RST}"
    # БД
    if DATABASE_URL:
        db_st = f"{G}✓ БД{RST}"
    else:
        db_st = f"{Y}✗ БД не задана{RST}"
    # Время
    t = time.strftime("%H:%M:%S")
    print(f"  Бот: {bot_st}   {db_st}   {DIM}{t}{RST}")
    divider()

# ── БД ────────────────────────────────────────────────────────────────────────
def get_db():
    if not DATABASE_URL:
        print(f"\n  {Y}⚠  DATABASE_URL не задан — открой [11] Настройки{RST}")
        return None
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"\n  {R}✗ Ошибка БД: {e}{RST}")
        return None

def db_query(sql, params=None, fetch="all"):
    conn = get_db()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch == "one":
                return cur.fetchone()
            return cur.fetchall()
    except Exception as e:
        print(f"  {R}✗ {e}{RST}")
        return None
    finally:
        conn.close()

def db_exec(sql, params=None):
    conn = get_db()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
        return True
    except Exception as e:
        print(f"  {R}✗ {e}{RST}")
        return False
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# ЭКРАНЫ
# ══════════════════════════════════════════════════════════════════════════════

# ── Главное меню ──────────────────────────────────────────────────────────────
def screen_main():
    header()
    status_bar()
    db_hint = f" {Y}← задай здесь{RST}" if not DATABASE_URL else ""

    sections = [
        ("", [
            (G,  "1", "🚀  Запустить бота"),
            (R,  "2", "⛔  Остановить бота"),
            (Y,  "3", "🔄  Перезапустить бота"),
        ]),
        ("  📊  БАЗА ДАННЫХ", [
            (C,  "4", "📊  Статистика"),
            (B,  "5", "👥  Пользователи"),
            (M,  "6", "📦  Заказы"),
            (W,  "7", "✅  Оплаченные подписки"),
            (C,  "8", "🔍  Найти пользователя"),
            (Y,  "9", "🗑   Очистить pending-заказы"),
        ]),
        ("  🛠   ИНСТРУМЕНТЫ", [
            (G,  "10", "📋  Логи бота (live)"),
            (C,  "11", "🔁  Обновить зависимости"),
            (Y,  "12", f"⚙️   Настройки{db_hint}"),
        ]),
    ]

    for title, items in sections:
        if title:
            print(f"\n{DIM}{title}{RST}")
        for col, key, label in items:
            kw = f"{key:>2}"
            print(f"  {col}[{kw}]{RST}  {label}")

    divider()
    print(f"  {R}[ 0]{RST}  ❌  Выход")
    return input(f"\n  {C}>{RST} ").strip()

# ── 1. Запуск ─────────────────────────────────────────────────────────────────
def action_start():
    global bot_process
    if bot_running():
        print(f"\n  {Y}⚠  Бот уже запущен (PID {bot_process.pid}){RST}")
        pause(); return
    env = os.environ.copy()
    env["TOKEN"] = TOKEN
    if DATABASE_URL:
        env["DATABASE_URL"] = DATABASE_URL
    loading("Запускаю бота...", 1.2)
    bot_process = subprocess.Popen(
        [sys.executable, BOT_SCRIPT], env=env,
        stdout=open(LOG_FILE, "a", encoding="utf-8"),
        stderr=subprocess.STDOUT
    )
    time.sleep(1.5)
    if bot_running():
        print(f"  {G}{BLD}✓ Бот успешно запущен!{RST}  PID: {bot_process.pid}")
    else:
        print(f"  {R}✗ Бот упал при старте. Смотри логи [10]{RST}")
    pause()

# ── 2. Остановка ──────────────────────────────────────────────────────────────
def action_stop(silent=False):
    global bot_process
    if not bot_running():
        if not silent:
            print(f"\n  {Y}⚠  Бот не запущен{RST}"); pause()
        return
    loading("Останавливаю бота...", 0.8)
    bot_process.terminate()
    try:
        bot_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        bot_process.kill()
    if not silent:
        print(f"  {G}✓ Бот остановлен{RST}"); pause()

# ── 3. Перезапуск ─────────────────────────────────────────────────────────────
def action_restart():
    action_stop(silent=True)
    time.sleep(0.5)
    action_start()

# ── 4. Статистика ─────────────────────────────────────────────────────────────
def screen_stats():
    header()
    loading("Загружаю статистику...", 0.8)
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as c FROM users"); u = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders"); ot = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='paid'"); op = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'"); opd = cur.fetchone()["c"]
            cur.execute("SELECT COALESCE(SUM(price),0) as s FROM orders WHERE status='paid'"); rev = cur.fetchone()["s"]
            cur.execute("SELECT COUNT(*) as c FROM subscriptions"); subs = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM users WHERE joined_at > NOW() - INTERVAL '24 hours'"); new24 = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='paid' AND created_at > NOW() - INTERVAL '24 hours'"); paid24 = cur.fetchone()["c"]
    except Exception as e:
        print(f"  {R}✗ {e}{RST}"); pause(); return
    finally:
        conn.close()

    divider("═", W)
    print(f"  {BLD}{W}📊  СТАТИСТИКА MorphVPN{RST}")
    divider("═", W)
    print(f"  {W}Всего пользователей:{RST}      {G}{BLD}{u}{RST}")
    print(f"  {W}Новых за 24ч:{RST}             {C}{new24}{RST}")
    print(f"  {W}Всего заказов:{RST}            {Y}{ot}{RST}")
    print(f"  {W}Оплачено:{RST}                 {G}{BLD}{op}{RST}")
    print(f"  {W}Ожидают оплаты:{RST}           {Y}{opd}{RST}")
    print(f"  {W}Оплат за 24ч:{RST}             {C}{paid24}{RST}")
    print(f"  {W}Активных подписок:{RST}        {G}{subs}{RST}")
    divider("─", C)
    print(f"  {W}💰 Общая выручка:{RST}         {G}{BLD}{rev} ₽{RST}")
    divider("═", W)
    pause()

# ── 5. Пользователи ───────────────────────────────────────────────────────────
def screen_users():
    header()
    loading("Загружаю пользователей...", 0.6)
    rows = db_query("SELECT user_id, username, first_name, joined_at FROM users ORDER BY joined_at DESC LIMIT 100")
    if rows is None: pause(); return
    if not rows:
        print(f"\n  {Y}Пользователей пока нет{RST}"); pause(); return
    print(f"\n  {C}{BLD}{'#':<4} {'ID':<14} {'Username':<22} {'Имя':<22} {'Дата'}{RST}")
    divider()
    for i, r in enumerate(rows, 1):
        uname = f"@{r['username']}" if r['username'] else f"{DIM}—{RST}"
        dt = str(r['joined_at'])[:16]
        print(f"  {DIM}{i:<4}{RST}{W}{r['user_id']:<14}{RST}{uname:<22} {r['first_name'] or '—':<22} {DIM}{dt}{RST}")
    divider()
    print(f"  {DIM}Показано: {len(rows)} из {db_query('SELECT COUNT(*) as c FROM users', fetch='one')['c']}{RST}")
    pause()

# ── 6. Заказы ─────────────────────────────────────────────────────────────────
def screen_orders():
    header()
    loading("Загружаю заказы...", 0.6)
    rows = db_query("""
        SELECT o.id, o.user_id, u.first_name, o.plan_name, o.price, o.status, o.created_at
        FROM orders o LEFT JOIN users u ON o.user_id=u.user_id
        ORDER BY o.created_at DESC LIMIT 100
    """)
    if rows is None: pause(); return
    if not rows:
        print(f"\n  {Y}Заказов нет{RST}"); pause(); return
    print(f"\n  {C}{BLD}{'#':<5} {'ID':<13} {'Имя':<18} {'Тариф':<12} {'₽':<7} {'Статус':<10} {'Дата'}{RST}")
    divider()
    for r in rows:
        sc = G if r['status'] == 'paid' else Y
        dt = str(r['created_at'])[:16]
        nm = (r['first_name'] or '—')[:17]
        print(f"  {DIM}{r['id']:<5}{RST}{W}{r['user_id']:<13}{RST} {nm:<18} {r['plan_name']:<12} {r['price']:<7} {sc}{r['status']:<10}{RST} {DIM}{dt}{RST}")
    divider()
    pause()

# ── 7. Оплаченные подписки ────────────────────────────────────────────────────
def screen_paid():
    header()
    loading("Загружаю подписки...", 0.6)
    rows = db_query("""
        SELECT s.id, s.user_id, u.first_name, u.username, s.plan_name, s.activated_at
        FROM subscriptions s LEFT JOIN users u ON s.user_id=u.user_id
        ORDER BY s.activated_at DESC LIMIT 100
    """)
    if rows is None: pause(); return
    if not rows:
        print(f"\n  {Y}Оплат пока нет{RST}"); pause(); return
    print(f"\n  {C}{BLD}{'#':<5} {'UserID':<14} {'Имя':<18} {'Username':<20} {'Тариф':<12} {'Дата'}{RST}")
    divider()
    for r in rows:
        uname = f"@{r['username']}" if r['username'] else "—"
        dt = str(r['activated_at'])[:16]
        print(f"  {G}{r['id']:<5}{RST}{W}{r['user_id']:<14}{RST} {(r['first_name'] or '—'):<18} {uname:<20} {r['plan_name']:<12} {DIM}{dt}{RST}")
    divider()
    pause()

# ── 8. Поиск пользователя ─────────────────────────────────────────────────────
def screen_search():
    header()
    q = input(f"\n  {C}Введи Telegram ID или @username:{RST} ").strip()
    if not q: return
    loading("Ищу...", 0.5)
    conn = get_db()
    if not conn: pause(); return
    try:
        with conn.cursor() as cur:
            if q.lstrip("@").isdigit():
                cur.execute("SELECT * FROM users WHERE user_id=%s", (int(q.lstrip("@")),))
            else:
                cur.execute("SELECT * FROM users WHERE username ILIKE %s", (f"%{q.lstrip('@')}%",))
            user = cur.fetchone()
        if not user:
            print(f"\n  {Y}Пользователь не найден{RST}"); pause(); return
        divider("═", W)
        print(f"  {BLD}{W}👤  ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ{RST}")
        divider("═", W)
        print(f"  {W}ID:{RST}           {G}{BLD}{user['user_id']}{RST}")
        print(f"  {W}Имя:{RST}          {user['first_name'] or '—'}")
        print(f"  {W}Username:{RST}     @{user['username'] or '—'}")
        print(f"  {W}Регистрация:{RST}  {str(user['joined_at'])[:16]}")
        divider()
        with conn.cursor() as cur:
            cur.execute("SELECT plan_name, price, status, created_at FROM orders WHERE user_id=%s ORDER BY created_at DESC", (user['user_id'],))
            orders = cur.fetchall()
        if orders:
            print(f"  {C}Заказы:{RST}")
            for o in orders:
                sc = G if o['status'] == 'paid' else Y
                print(f"    {o['plan_name']:<14} {o['price']}₽  {sc}{o['status']}{RST}  {DIM}{str(o['created_at'])[:16]}{RST}")
        else:
            print(f"  {DIM}Заказов нет{RST}")
        divider("═", W)
    except Exception as e:
        print(f"  {R}✗ {e}{RST}")
    finally:
        conn.close()
    pause()

# ── 9. Очистить pending ───────────────────────────────────────────────────────
def action_clear_pending():
    header()
    row = db_query("SELECT COUNT(*) as c FROM orders WHERE status='pending'", fetch="one")
    if row is None: pause(); return
    cnt = row["c"]
    if cnt == 0:
        print(f"\n  {G}Нет pending-заказов — всё чисто{RST}"); pause(); return
    print(f"\n  {Y}Найдено {cnt} незавершённых заказов{RST}")
    ans = input(f"  {R}Удалить все? (да/нет):{RST} ").strip().lower()
    if ans in ("да", "y", "yes"):
        loading("Удаляю...", 0.8)
        if db_exec("DELETE FROM orders WHERE status='pending'"):
            print(f"  {G}✓ Удалено {cnt} заказов{RST}")
        else:
            print(f"  {R}✗ Ошибка удаления{RST}")
    else:
        print(f"  {DIM}Отменено{RST}")
    pause()

# ── 10. Логи (live) ───────────────────────────────────────────────────────────
def screen_logs():
    header()
    if not os.path.exists(LOG_FILE):
        print(f"\n  {Y}bot.log не найден — сначала запусти бота [1]{RST}"); pause(); return

    print(f"  {DIM}Показываю последние 50 строк. Нажми Ctrl+C для выхода.{RST}\n")
    divider()
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-50:]
        for line in lines:
            line = line.rstrip()
            if "ERROR" in line:   print(f"  {R}{line}{RST}")
            elif "WARNING" in line: print(f"  {Y}{line}{RST}")
            elif "INFO" in line:  print(f"  {DIM}{line}{RST}")
            else:                 print(f"  {line}")
        divider()
        print(f"\n  {DIM}[L] Очистить лог   [Enter] Назад{RST}")
        ch = input("  > ").strip().lower()
        if ch == "l":
            open(LOG_FILE, "w").close()
            print(f"  {G}✓ Лог очищен{RST}")
            time.sleep(0.8)
    except KeyboardInterrupt:
        pass

# ── 11. Обновить зависимости ──────────────────────────────────────────────────
def action_update_deps():
    header()
    req = os.path.join(BASE, "requirements.txt")
    print(f"\n  {C}Обновляю зависимости из requirements.txt...{RST}\n")
    divider()
    if os.path.exists(req):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req, "--upgrade"])
    else:
        subprocess.run([sys.executable, "-m", "pip", "install",
                        "python-telegram-bot==20.3", "psycopg2-binary", "colorama", "--upgrade"])
    divider()
    print(f"\n  {G}✓ Готово{RST}")
    pause()

# ── 12. Настройки ─────────────────────────────────────────────────────────────
def screen_settings():
    global TOKEN, DATABASE_URL
    while True:
        header()
        db_short = (DATABASE_URL[:50] + "...") if len(DATABASE_URL) > 50 else (DATABASE_URL or f"{R}НЕ ЗАДАН{RST}")
        tok_short = TOKEN[:25] + "..." if len(TOKEN) > 25 else TOKEN

        divider("═", W)
        print(f"  {BLD}{W}⚙️   НАСТРОЙКИ{RST}")
        divider("═", W)
        print(f"  {W}TOKEN:{RST}")
        print(f"    {DIM}{tok_short}{RST}")
        print(f"  {W}DATABASE_URL:{RST}")
        print(f"    {Y if not DATABASE_URL else DIM}{db_short}{RST}")
        divider()
        print(f"\n  {W}[1]{RST}  Изменить TOKEN")
        print(f"  {W}[2]{RST}  Изменить DATABASE_URL")
        print(f"  {W}[3]{RST}  Проверить подключение к БД")
        print(f"  {W}[4]{RST}  Открыть .env в блокноте")
        print(f"  {R}[0]{RST}  Назад")
        ch = input(f"\n  {C}>{RST} ").strip()

        if ch == "1":
            print(f"\n  {DIM}Текущий: {TOKEN[:20]}...{RST}")
            val = input("  Новый TOKEN: ").strip()
            if val:
                TOKEN = val; os.environ["TOKEN"] = val; save_env()
                print(f"  {G}✓ TOKEN сохранён{RST}"); time.sleep(1)
        elif ch == "2":
            print(f"\n  {C}Где найти:{RST} Railway → проект → PostgreSQL → Variables → DATABASE_URL")
            val = input("  Вставь DATABASE_URL: ").strip()
            if val:
                DATABASE_URL = val; os.environ["DATABASE_URL"] = val; save_env()
                print(f"  {G}✓ DATABASE_URL сохранён{RST}"); time.sleep(1)
        elif ch == "3":
            loading("Проверяю подключение...", 1.0)
            conn = get_db()
            if conn:
                print(f"  {G}✓ Подключение успешно!{RST}"); conn.close()
            time.sleep(1.2)
        elif ch == "4":
            if not os.path.exists(ENV_FILE):
                save_env()
            os.startfile(ENV_FILE) if os.name == "nt" else subprocess.run(["xdg-open", ENV_FILE])
            time.sleep(0.5)
        elif ch == "0":
            break

# ══════════════════════════════════════════════════════════════════════════════
# СПЛЭШ-ЭКРАН
# ══════════════════════════════════════════════════════════════════════════════
def splash():
    cls()
    logo = f"""
{C}{BLD}
    ███╗   ███╗ ██████╗ ██████╗ ██████╗ ██╗  ██╗██╗   ██╗██████╗ ███╗   ██╗
    ████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██║  ██║██║   ██║██╔══██╗████╗  ██║
    ██╔████╔██║██║   ██║██████╔╝██████╔╝███████║██║   ██║██████╔╝██╔██╗ ██║
    ██║╚██╔╝██║██║   ██║██╔══██╗██╔═══╝ ██╔══██║╚██╗ ██╔╝██╔═══╝ ██║╚██╗██║
    ██║ ╚═╝ ██║╚██████╔╝██║  ██║██║     ██║  ██║ ╚████╔╝ ██║     ██║ ╚████║
    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝  ╚═══╝  ╚═╝     ╚═╝  ╚═══╝
{RST}"""
    print(logo)
    print(f"  {W}                  Панель управления ботом  v2.0{RST}")
    print(f"  {DIM}                  Telegram: @MorphVPN1_bot{RST}\n")
    divider("─", DIM)

    steps = [
        "Загружаю конфигурацию...",
        "Подключаюсь к базе данных...",
        "Проверяю зависимости...",
        "Готово!",
    ]
    for step in steps:
        loading(step, 0.6)
    time.sleep(0.3)

# ══════════════════════════════════════════════════════════════════════════════
# ГЛАВНЫЙ ЦИКЛ
# ══════════════════════════════════════════════════════════════════════════════
def main():
    load_env()
    splash()

    dispatch = {
        "1":  action_start,
        "2":  action_stop,
        "3":  action_restart,
        "4":  screen_stats,
        "5":  screen_users,
        "6":  screen_orders,
        "7":  screen_paid,
        "8":  screen_search,
        "9":  action_clear_pending,
        "10": screen_logs,
        "11": action_update_deps,
        "12": screen_settings,
    }

    while True:
        try:
            choice = screen_main()
            if choice == "0":
                action_stop(silent=True)
                cls()
                print(f"\n  {G}До свидания! MorphVPN всегда на страже 🔒{RST}\n")
                sys.exit(0)
            fn = dispatch.get(choice)
            if fn:
                fn()
            else:
                time.sleep(0.3)
        except KeyboardInterrupt:
            print(f"\n\n  {Y}Ctrl+C — используй [0] для выхода{RST}")
            time.sleep(1)

if __name__ == "__main__":
    main()

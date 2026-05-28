# -*- coding: utf-8 -*-
"""
MorphVPN Launcher — GUI панель управления
"""
import os, sys, subprocess, threading, time, webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ── Авто-установка зависимостей ───────────────────────────────────────────────
def install(pkg):
    subprocess.run([sys.executable, "-m", "pip", "install", pkg, "-q"], check=False)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    install("psycopg2-binary")
    import psycopg2
    from psycopg2.extras import RealDictCursor

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Конфиг ────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE, ".env")
BOT_FILE = os.path.join(BASE, "bot.py")
LOG_FILE = os.path.join(BASE, "bot.log")
SITE_URL = "https://morphvpn-production.up.railway.app"

TOKEN        = "8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA"
DATABASE_URL = ""
bot_process  = None

# ── Цвета ─────────────────────────────────────────────────────────────────────
BG       = "#0a0e27"
BG2      = "#12172e"
BG3      = "#1a1f3a"
CARD     = "#1e2440"
CYAN     = "#00d4ff"
PINK     = "#ff006e"
GREEN    = "#00ff78"
YELLOW   = "#ffcc00"
WHITE    = "#e0e6ff"
GRAY     = "#6b7280"
FONT     = "Segoe UI"

def load_env():
    global TOKEN, DATABASE_URL
    if not os.path.exists(ENV_FILE): return
    with open(ENV_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, _, v = line.partition("=")
            k=k.strip(); v=v.strip().strip('"').strip("'")
            if k=="TOKEN" and v: TOKEN=v
            if k=="DATABASE_URL" and v: DATABASE_URL=v

def save_env():
    with open(ENV_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"TOKEN={TOKEN}\n")
        f.write(f"DATABASE_URL={DATABASE_URL}\n")

def get_db():
    if not DATABASE_URL: return None
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except: return None

# ══════════════════════════════════════════════════════════════════════════════
# ГЛАВНОЕ ОКНО
# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MorphVPN — Панель управления")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.resizable(True, True)
        self._center()
        self._build_ui()
        self._refresh_status()
        self.after(5000, self._auto_refresh)

    def _center(self):
        self.update_idletasks()
        w,h = 1100,700
        x = (self.winfo_screenwidth()-w)//2
        y = (self.winfo_screenheight()-h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # ── Шапка ─────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG2, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔒 MorphVPN", font=(FONT, 22, "bold"),
                 bg=BG2, fg=CYAN).pack(side="left", padx=20, pady=15)
        tk.Label(header, text="Панель управления v3.0", font=(FONT, 11),
                 bg=BG2, fg=GRAY).pack(side="left", padx=5, pady=15)

        # Статус бота в шапке
        self.lbl_bot_status = tk.Label(header, text="● БОТ ОСТАНОВЛЕН",
                                        font=(FONT, 10, "bold"), bg=BG2, fg=PINK)
        self.lbl_bot_status.pack(side="right", padx=20)

        # ── Основной layout ───────────────────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Левая панель — навигация
        nav = tk.Frame(main, bg=BG2, width=200)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)

        # Правая панель — контент
        self.content = tk.Frame(main, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # ── Навигация ─────────────────────────────────────────────────────────
        tk.Label(nav, text="МЕНЮ", font=(FONT, 9), bg=BG2, fg=GRAY
                 ).pack(pady=(20,5), padx=15, anchor="w")

        nav_items = [
            ("🏠  Главная",       self.page_home),
            ("📊  Статистика",    self.page_stats),
            ("👥  Пользователи",  self.page_users),
            ("📦  Заказы",        self.page_orders),
            ("✅  Оплаты",        self.page_paid),
            ("🌐  Сайт",          self.page_site),
            ("📋  Логи бота",     self.page_logs),
            ("⚙️   Настройки",    self.page_settings),
        ]
        self.nav_btns = []
        for label, cmd in nav_items:
            btn = tk.Button(nav, text=label, font=(FONT, 11),
                            bg=BG2, fg=WHITE, bd=0, cursor="hand2",
                            activebackground=BG3, activeforeground=CYAN,
                            anchor="w", padx=15, pady=10,
                            command=lambda c=cmd, b=None: self._nav_click(c))
            btn.pack(fill="x")
            self.nav_btns.append((btn, cmd))

        # Версия внизу
        tk.Label(nav, text="v3.0 © MorphVPN", font=(FONT, 8),
                 bg=BG2, fg=GRAY).pack(side="bottom", pady=10)

        # Показываем главную
        self.update()
        self.page_home()

    def _nav_click(self, cmd):
        for btn, c in self.nav_btns:
            if c == cmd:
                btn.configure(bg=BG3, fg=CYAN)
            else:
                btn.configure(bg=BG2, fg=WHITE)
        cmd()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _auto_refresh(self):
        self._refresh_status()
        self.after(5000, self._auto_refresh)

    def _refresh_status(self):
        global bot_process
        if bot_process and bot_process.poll() is None:
            self.lbl_bot_status.configure(text="● БОТ ЗАПУЩЕН", fg=GREEN)
        else:
            self.lbl_bot_status.configure(text="● БОТ ОСТАНОВЛЕН", fg=PINK)

    # ── Карточка ──────────────────────────────────────────────────────────────
    def _card(self, parent, title="", col=CYAN):
        frame = tk.Frame(parent, bg=CARD, bd=0)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        if title:
            tk.Label(frame, text=title, font=(FONT, 10, "bold"),
                     bg=CARD, fg=col).pack(anchor="w", padx=12, pady=(10,2))
            tk.Frame(frame, bg=col, height=1).pack(fill="x", padx=12, pady=(0,8))
        return frame

    def _stat_box(self, parent, label, value, color=CYAN):
        box = tk.Frame(parent, bg=BG3, padx=15, pady=12)
        box.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        tk.Label(box, text=str(value), font=(FONT, 28, "bold"),
                 bg=BG3, fg=color).pack()
        tk.Label(box, text=label, font=(FONT, 9),
                 bg=BG3, fg=GRAY).pack()
        return box

    def _btn(self, parent, text, cmd, color=CYAN, width=18):
        def on_enter(e): b.configure(bg=color, fg=BG)
        def on_leave(e): b.configure(bg=BG3, fg=color)
        b = tk.Button(parent, text=text, font=(FONT, 10, "bold"),
                      bg=BG3, fg=color, bd=0, cursor="hand2",
                      width=width, pady=8, command=cmd,
                      relief="flat", activebackground=color, activeforeground=BG)
        b.bind("<Enter>", on_enter)
        b.bind("<Leave>", on_leave)
        b.pack(side="left", padx=5, pady=5)
        return b

    def _table(self, parent, columns, rows, col_widths=None):
        frame = tk.Frame(parent, bg=CARD)
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        # Скролл
        vsb = ttk.Scrollbar(frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        hsb.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
            background=CARD, foreground=WHITE,
            fieldbackground=CARD, rowheight=28,
            font=(FONT, 10))
        style.configure("Dark.Treeview.Heading",
            background=BG3, foreground=CYAN,
            font=(FONT, 10, "bold"), relief="flat")
        style.map("Dark.Treeview",
            background=[("selected", BG3)],
            foreground=[("selected", CYAN)])

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            style="Dark.Treeview",
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        for i, col in enumerate(columns):
            w = col_widths[i] if col_widths else 120
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=60)

        for row in rows:
            tree.insert("", "end", values=row)

        tree.pack(fill="both", expand=True)
        return tree

    # ══════════════════════════════════════════════════════════════════════════
    # СТРАНИЦЫ
    # ══════════════════════════════════════════════════════════════════════════

    def page_home(self):
        self._clear_content()
        c = self.content

        tk.Label(c, text="Добро пожаловать в MorphVPN", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,5), padx=20, anchor="w")
        tk.Label(c, text="Управляй ботом, смотри статистику и данные из БД",
                 font=(FONT,10), bg=BG, fg=GRAY).pack(padx=20, anchor="w")

        # Кнопки управления ботом
        btn_frame = tk.Frame(c, bg=BG)
        btn_frame.pack(fill="x", padx=20, pady=15)
        self._btn(btn_frame, "🚀  Запустить бота",   self.start_bot, GREEN)
        self._btn(btn_frame, "⛔  Остановить бота",  self.stop_bot,  PINK)
        self._btn(btn_frame, "🔄  Перезапустить",    self.restart_bot, YELLOW)
        self._btn(btn_frame, "🌐  Открыть сайт",
                  lambda: webbrowser.open(SITE_URL), CYAN)

        # Статистика — загружаем в потоке
        stats_frame = tk.Frame(c, bg=BG)
        stats_frame.pack(fill="x", padx=20, pady=5)

        # Заглушки
        boxes = {}
        for key, lbl, col in [
            ("u","Пользователей бота",CYAN),
            ("p","Оплачено заказов",GREEN),
            ("r","Выручка (₽)",YELLOW),
            ("v","Посещений сайта",CYAN),
            ("ct","Заявок с сайта",PINK),
        ]:
            boxes[key] = self._stat_box(stats_frame, lbl, "...", col)

        # Таблица заголовок
        tk.Label(c, text="Последние заказы", font=(FONT,12,"bold"),
                 bg=BG, fg=WHITE).pack(padx=20, pady=(15,5), anchor="w")

        table_frame = tk.Frame(c, bg=BG)
        table_frame.pack(fill="both", expand=True)
        loading_lbl = tk.Label(table_frame, text="Загрузка данных...",
                               font=(FONT,11), bg=BG, fg=GRAY)
        loading_lbl.pack(pady=30)

        def load_data():
            conn = get_db()
            u=o=p=r=v=ct=0; rows=[]
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) as c FROM users"); u=cur.fetchone()["c"]
                        cur.execute("SELECT COUNT(*) as c FROM orders"); o=cur.fetchone()["c"]
                        cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='paid'"); p=cur.fetchone()["c"]
                        cur.execute("SELECT COALESCE(SUM(price),0) as s FROM orders WHERE status='paid'"); r=cur.fetchone()["s"]
                        cur.execute("SELECT COUNT(*) as c FROM visits"); v=cur.fetchone()["c"]
                        cur.execute("SELECT COUNT(*) as c FROM contacts"); ct=cur.fetchone()["c"]
                        cur.execute("""SELECT o.id,u.first_name,o.plan_name,o.price,o.status,
                                       to_char(o.created_at,'DD.MM.YY HH24:MI') as dt
                                       FROM orders o LEFT JOIN users u ON o.user_id=u.user_id
                                       ORDER BY o.created_at DESC LIMIT 8""")
                        rows=[(r2["id"],r2["first_name"] or "—",r2["plan_name"],
                               f"{r2['price']}₽",r2["status"],r2["dt"]) for r2 in cur.fetchall()]
                except: pass
                finally: conn.close()

            def update_ui():
                for widget in boxes["u"].winfo_children():
                    if isinstance(widget, tk.Label) and widget.cget("font") and "28" in str(widget.cget("font")):
                        widget.configure(text=str(u)); break
                # Обновляем все боксы
                def upd(box, val):
                    for w in box.winfo_children():
                        try:
                            if "28" in str(w.cget("font")):
                                w.configure(text=str(val)); return
                        except: pass
                upd(boxes["u"], u); upd(boxes["p"], p)
                upd(boxes["r"], r); upd(boxes["v"], v); upd(boxes["ct"], ct)
                loading_lbl.destroy()
                self._table(table_frame, ["#","Имя","Тариф","Цена","Статус","Дата"],
                            rows, [40,120,100,70,80,120])
            self.after(0, update_ui)

        threading.Thread(target=load_data, daemon=True).start()

    # ── Статистика ────────────────────────────────────────────────────────────
    def page_stats(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="📊 Статистика", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,15), padx=20, anchor="w")

        conn = get_db()
        if not conn:
            tk.Label(c, text="❌ База данных не подключена\nОткрой Настройки и добавь DATABASE_URL",
                     font=(FONT,12), bg=BG, fg=PINK).pack(pady=50)
            return

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as c FROM users"); u=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM orders"); ot=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='paid'"); op=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM orders WHERE status='pending'"); opd=cur.fetchone()["c"]
                cur.execute("SELECT COALESCE(SUM(price),0) as s FROM orders WHERE status='paid'"); rev=cur.fetchone()["s"]
                cur.execute("SELECT COUNT(*) as c FROM subscriptions"); subs=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM users WHERE joined_at > NOW()-INTERVAL '24 hours'"); new24=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM visits"); vis=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM visits WHERE created_at > NOW()-INTERVAL '24 hours'"); vis24=cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) as c FROM contacts"); cont=cur.fetchone()["c"]
                cur.execute("SELECT page, COUNT(*) as c FROM visits GROUP BY page ORDER BY c DESC LIMIT 5"); pages=cur.fetchall()
        except Exception as e:
            tk.Label(c, text=f"Ошибка: {e}", bg=BG, fg=PINK).pack()
            return
        finally: conn.close()

        # Ряд 1
        r1 = tk.Frame(c, bg=BG); r1.pack(fill="x", padx=20)
        self._stat_box(r1, "Пользователей",    u,    CYAN)
        self._stat_box(r1, "Новых за 24ч",     new24, GREEN)
        self._stat_box(r1, "Всего заказов",    ot,   YELLOW)
        self._stat_box(r1, "Оплачено",         op,   GREEN)

        # Ряд 2
        r2 = tk.Frame(c, bg=BG); r2.pack(fill="x", padx=20)
        self._stat_box(r2, "Ожидают оплаты",   opd,  YELLOW)
        self._stat_box(r2, "Подписок",         subs, CYAN)
        self._stat_box(r2, "Выручка ₽",        rev,  GREEN)
        self._stat_box(r2, "Посещений сайта",  vis,  CYAN)

        # Топ страниц
        tk.Label(c, text="Топ страниц сайта", font=(FONT,12,"bold"),
                 bg=BG, fg=WHITE).pack(padx=20, pady=(15,5), anchor="w")
        rows = [(r["page"], r["c"]) for r in pages]
        self._table(c, ["Страница","Посещений"], rows, [300,100])

    # ── Пользователи ──────────────────────────────────────────────────────────
    def page_users(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="👥 Пользователи бота", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,5), padx=20, anchor="w")

        # Поиск
        sf = tk.Frame(c, bg=BG); sf.pack(fill="x", padx=20, pady=8)
        tk.Label(sf, text="Поиск:", font=(FONT,10), bg=BG, fg=GRAY).pack(side="left")
        self.search_var = tk.StringVar()
        entry = tk.Entry(sf, textvariable=self.search_var, font=(FONT,10),
                         bg=BG3, fg=WHITE, insertbackground=WHITE,
                         bd=0, width=25)
        entry.pack(side="left", padx=8, ipady=5)
        self._btn(sf, "🔍 Найти", lambda: self._load_users(c), CYAN, 10)
        self._btn(sf, "↺ Все",   lambda: [self.search_var.set(""), self._load_users(c)], GRAY, 8)

        self._load_users(c)

    def _load_users(self, parent):
        # Удаляем старую таблицу
        for w in parent.winfo_children():
            if isinstance(w, tk.Frame) and hasattr(w, "_is_table"):
                w.destroy()

        conn = get_db()
        rows = []
        if conn:
            try:
                q = self.search_var.get().strip()
                with conn.cursor() as cur:
                    if q.isdigit():
                        cur.execute("SELECT user_id,username,first_name,joined_at FROM users WHERE user_id=%s", (int(q),))
                    elif q:
                        cur.execute("SELECT user_id,username,first_name,joined_at FROM users WHERE username ILIKE %s OR first_name ILIKE %s ORDER BY joined_at DESC LIMIT 100", (f"%{q}%",f"%{q}%"))
                    else:
                        cur.execute("SELECT user_id,username,first_name,joined_at FROM users ORDER BY joined_at DESC LIMIT 100")
                    rows = [(r["user_id"], f"@{r['username']}" if r["username"] else "—",
                             r["first_name"] or "—",
                             str(r["joined_at"])[:16]) for r in cur.fetchall()]
            except: pass
            finally: conn.close()

        f = tk.Frame(parent, bg=BG)
        f._is_table = True
        f.pack(fill="both", expand=True)
        self._table(f, ["ID","Username","Имя","Дата регистрации"],
                    rows, [130,160,160,140])

    # ── Заказы ────────────────────────────────────────────────────────────────
    def page_orders(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="📦 Заказы", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,5), padx=20, anchor="w")

        # Фильтр
        ff = tk.Frame(c, bg=BG); ff.pack(fill="x", padx=20, pady=8)
        self.order_filter = tk.StringVar(value="all")
        for val, lbl in [("all","Все"),("paid","Оплачено"),("pending","Ожидают")]:
            tk.Radiobutton(ff, text=lbl, variable=self.order_filter, value=val,
                           font=(FONT,10), bg=BG, fg=WHITE,
                           selectcolor=BG3, activebackground=BG,
                           command=lambda: self._load_orders(c)).pack(side="left", padx=8)

        self._load_orders(c)

    def _load_orders(self, parent):
        for w in parent.winfo_children():
            if isinstance(w, tk.Frame) and hasattr(w, "_is_table"):
                w.destroy()

        conn = get_db(); rows = []
        if conn:
            try:
                f = self.order_filter.get()
                with conn.cursor() as cur:
                    sql = """SELECT o.id,u.first_name,o.plan_name,o.price,o.status,
                             to_char(o.created_at,'DD.MM.YY HH24:MI') as dt
                             FROM orders o LEFT JOIN users u ON o.user_id=u.user_id"""
                    if f != "all": sql += f" WHERE o.status='{f}'"
                    sql += " ORDER BY o.created_at DESC LIMIT 100"
                    cur.execute(sql)
                    rows = [(r["id"],r["first_name"] or "—",r["plan_name"],
                             f"{r['price']}₽",r["status"],r["dt"]) for r in cur.fetchall()]
            except: pass
            finally: conn.close()

        fr = tk.Frame(parent, bg=BG); fr._is_table=True; fr.pack(fill="both", expand=True)
        self._table(fr, ["#","Имя","Тариф","Цена","Статус","Дата"],
                    rows, [40,130,110,70,90,120])

    # ── Оплаты ────────────────────────────────────────────────────────────────
    def page_paid(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="✅ Подтверждённые оплаты", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,15), padx=20, anchor="w")

        conn = get_db(); rows = []
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT s.id,u.first_name,u.username,s.plan_name,
                               to_char(s.activated_at,'DD.MM.YY HH24:MI') as dt
                        FROM subscriptions s LEFT JOIN users u ON s.user_id=u.user_id
                        ORDER BY s.activated_at DESC LIMIT 100
                    """)
                    rows = [(r["id"],r["first_name"] or "—",
                             f"@{r['username']}" if r["username"] else "—",
                             r["plan_name"],r["dt"]) for r in cur.fetchall()]
            except: pass
            finally: conn.close()

        self._table(c, ["#","Имя","Username","Тариф","Дата"],
                    rows, [40,140,160,120,130])

    # ── Сайт ──────────────────────────────────────────────────────────────────
    def page_site(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="🌐 Статистика сайта", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,15), padx=20, anchor="w")

        conn = get_db(); vis=vis24=cont=0; pages=[]; contacts=[]
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) as c FROM visits"); vis=cur.fetchone()["c"]
                    cur.execute("SELECT COUNT(*) as c FROM visits WHERE created_at>NOW()-INTERVAL '24 hours'"); vis24=cur.fetchone()["c"]
                    cur.execute("SELECT COUNT(*) as c FROM contacts"); cont=cur.fetchone()["c"]
                    cur.execute("SELECT page,COUNT(*) as c FROM visits GROUP BY page ORDER BY c DESC LIMIT 20"); pages=cur.fetchall()
                    cur.execute("SELECT name,email,message,to_char(created_at,'DD.MM.YY HH24:MI') as dt FROM contacts ORDER BY created_at DESC LIMIT 50"); contacts=cur.fetchall()
            except: pass
            finally: conn.close()

        r1 = tk.Frame(c, bg=BG); r1.pack(fill="x", padx=20)
        self._stat_box(r1, "Всего посещений", vis,  CYAN)
        self._stat_box(r1, "За 24 часа",      vis24, GREEN)
        self._stat_box(r1, "Заявок с формы",  cont, PINK)

        tk.Label(c, text="Топ страниц", font=(FONT,12,"bold"),
                 bg=BG, fg=WHITE).pack(padx=20, pady=(15,5), anchor="w")
        self._table(c, ["Страница","Посещений"],
                    [(r["page"],r["c"]) for r in pages], [350,100])

        tk.Label(c, text="Заявки с сайта", font=(FONT,12,"bold"),
                 bg=BG, fg=WHITE).pack(padx=20, pady=(15,5), anchor="w")
        self._table(c, ["Имя","Email","Сообщение","Дата"],
                    [(r["name"],r["email"],r["message"][:40]+"…" if len(r["message"])>40 else r["message"],r["dt"]) for r in contacts],
                    [120,160,250,120])

    # ── Логи ──────────────────────────────────────────────────────────────────
    def page_logs(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="📋 Логи бота", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,5), padx=20, anchor="w")

        bf = tk.Frame(c, bg=BG); bf.pack(fill="x", padx=20, pady=5)
        self._btn(bf, "🔄 Обновить", lambda: self._reload_logs(txt), CYAN, 12)
        self._btn(bf, "🗑 Очистить", lambda: self._clear_logs(txt),  PINK, 12)

        txt = scrolledtext.ScrolledText(c, font=("Consolas",9),
                                         bg="#0d1117", fg="#c9d1d9",
                                         insertbackground=WHITE, bd=0,
                                         state="disabled")
        txt.pack(fill="both", expand=True, padx=20, pady=10)
        self._reload_logs(txt)

    def _reload_logs(self, txt):
        txt.configure(state="normal"); txt.delete("1.0","end")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE,"r",encoding="utf-8",errors="ignore") as f:
                lines = f.readlines()[-100:]
            for line in lines:
                tag = "err" if "ERROR" in line else ("warn" if "WARNING" in line else "info")
                txt.insert("end", line, tag)
            txt.tag_configure("err",  foreground="#ff6b6b")
            txt.tag_configure("warn", foreground="#ffcc00")
            txt.tag_configure("info", foreground="#8b949e")
            txt.see("end")
        else:
            txt.insert("end", "bot.log не найден. Запусти бота.\n")
        txt.configure(state="disabled")

    def _clear_logs(self, txt):
        open(LOG_FILE,"w").close()
        self._reload_logs(txt)

    # ── Настройки ─────────────────────────────────────────────────────────────
    def page_settings(self):
        self._clear_content()
        c = self.content
        tk.Label(c, text="⚙️ Настройки", font=(FONT,18,"bold"),
                 bg=BG, fg=WHITE).pack(pady=(25,15), padx=20, anchor="w")

        form = tk.Frame(c, bg=BG); form.pack(fill="x", padx=20)

        def field(label, default, show=""):
            tk.Label(form, text=label, font=(FONT,10), bg=BG, fg=GRAY
                     ).pack(anchor="w", pady=(10,2))
            var = tk.StringVar(value=default)
            e = tk.Entry(form, textvariable=var, font=(FONT,10),
                         bg=BG3, fg=WHITE, insertbackground=WHITE,
                         bd=0, width=70, show=show)
            e.pack(fill="x", ipady=7, pady=(0,2))
            tk.Frame(form, bg=CYAN, height=1).pack(fill="x")
            return var

        self.v_token = field("Telegram Bot TOKEN", TOKEN)
        self.v_db    = field("DATABASE_URL (Railway PostgreSQL)", DATABASE_URL)

        def save():
            global TOKEN, DATABASE_URL
            TOKEN = self.v_token.get().strip()
            DATABASE_URL = self.v_db.get().strip()
            save_env()
            messagebox.showinfo("Сохранено", "Настройки сохранены!")

        def test_db():
            conn = get_db()
            if conn:
                messagebox.showinfo("✅ Успех", "Подключение к БД успешно!")
                conn.close()
            else:
                messagebox.showerror("❌ Ошибка", "Не удалось подключиться к БД.\nПроверь DATABASE_URL")

        bf = tk.Frame(c, bg=BG); bf.pack(fill="x", padx=20, pady=15)
        self._btn(bf, "💾 Сохранить",      save,    GREEN, 16)
        self._btn(bf, "🔌 Проверить БД",   test_db, CYAN,  16)
        self._btn(bf, "🌐 Открыть сайт",
                  lambda: webbrowser.open(SITE_URL), CYAN, 16)
        self._btn(bf, "📊 API статистика",
                  lambda: webbrowser.open(f"{SITE_URL}/api/stats?key=morphvpn2026"), YELLOW, 18)

    # ── Управление ботом ──────────────────────────────────────────────────────
    def start_bot(self):
        global bot_process
        if bot_process and bot_process.poll() is None:
            messagebox.showinfo("Инфо", "Бот уже запущен!"); return
        env = os.environ.copy()
        env["TOKEN"] = TOKEN
        if DATABASE_URL: env["DATABASE_URL"] = DATABASE_URL
        bot_process = subprocess.Popen(
            [sys.executable, BOT_FILE], env=env,
            stdout=open(LOG_FILE,"a",encoding="utf-8"),
            stderr=subprocess.STDOUT)
        time.sleep(1)
        if bot_process.poll() is None:
            self._refresh_status()
            messagebox.showinfo("✅ Запущен", f"Бот запущен! PID: {bot_process.pid}")
        else:
            messagebox.showerror("❌ Ошибка", "Бот не запустился. Проверь логи.")

    def stop_bot(self):
        global bot_process
        if not bot_process or bot_process.poll() is not None:
            messagebox.showinfo("Инфо", "Бот не запущен"); return
        bot_process.terminate()
        bot_process.wait(timeout=5)
        self._refresh_status()
        messagebox.showinfo("✅ Остановлен", "Бот остановлен")

    def restart_bot(self):
        global bot_process
        if bot_process and bot_process.poll() is None:
            bot_process.terminate()
            bot_process.wait(timeout=5)
        time.sleep(0.5)
        self.start_bot()


# ══════════════════════════════════════════════════════════════════════════════
# СПЛЭШ
# ══════════════════════════════════════════════════════════════════════════════
class Splash(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        w,h = 500,300
        x=(self.winfo_screenwidth()-w)//2
        y=(self.winfo_screenheight()-h)//2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(bg=BG)

        tk.Label(self, text="🔒", font=(FONT,48), bg=BG, fg=CYAN).pack(pady=(40,5))
        tk.Label(self, text="MorphVPN", font=(FONT,24,"bold"), bg=BG, fg=WHITE).pack()
        tk.Label(self, text="Панель управления", font=(FONT,11), bg=BG, fg=GRAY).pack()

        self.prog_var = tk.DoubleVar()
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Cyan.Horizontal.TProgressbar",
                         troughcolor=BG3, background=CYAN, thickness=4)
        pb = ttk.Progressbar(self, variable=self.prog_var, maximum=100,
                              style="Cyan.Horizontal.TProgressbar", length=300)
        pb.pack(pady=20)
        self.lbl = tk.Label(self, text="Загрузка...", font=(FONT,9), bg=BG, fg=GRAY)
        self.lbl.pack()

        self._animate(0)

    def _animate(self, val):
        steps = [(20,"Загружаю конфигурацию..."),(50,"Подключаюсь к БД..."),
                 (80,"Инициализирую интерфейс..."),(100,"Готово!")]
        for target, msg in steps:
            if val <= target:
                self.prog_var.set(val)
                self.lbl.configure(text=msg)
                break
        if val < 100:
            self.after(30, lambda: self._animate(val+2))
        else:
            self.after(400, self._done)

    def _done(self):
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    load_env()
    app = App()
    app.mainloop()

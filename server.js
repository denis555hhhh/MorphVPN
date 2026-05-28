const express = require('express');
const path = require('path');
const { Pool } = require('pg');

const app = express();
app.use(express.static(path.join(__dirname)));
app.use(express.json());

// ── PostgreSQL ────────────────────────────────────────────────────────────────
const pool = process.env.DATABASE_URL
    ? new Pool({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } })
    : null;

async function initDB() {
    if (!pool) return;
    try {
        await pool.query(`
            CREATE TABLE IF NOT EXISTS visits (
                id          SERIAL PRIMARY KEY,
                page        TEXT NOT NULL,
                ip          TEXT,
                user_agent  TEXT,
                referer     TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        `);
        await pool.query(`
            CREATE TABLE IF NOT EXISTS contacts (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT NOT NULL,
                message     TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        `);
        console.log('✅ База данных инициализирована');
    } catch (e) {
        console.error('❌ Ошибка БД:', e.message);
    }
}

// ── Middleware: трекинг посещений ─────────────────────────────────────────────
app.use(async (req, res, next) => {
    if (pool && req.method === 'GET' && !req.path.startsWith('/api')) {
        const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
        const ua = req.headers['user-agent'] || '';
        const ref = req.headers['referer'] || '';
        pool.query(
            'INSERT INTO visits (page, ip, user_agent, referer) VALUES ($1,$2,$3,$4)',
            [req.path, ip, ua, ref]
        ).catch(() => {});
    }
    next();
});

// ── Страницы ──────────────────────────────────────────────────────────────────
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));
app.get('/privacy', (req, res) => res.sendFile(path.join(__dirname, 'privacy.html')));
app.get('/terms', (req, res) => res.sendFile(path.join(__dirname, 'terms.html')));
app.get('/status', (req, res) => res.sendFile(path.join(__dirname, 'status.html')));

// ── API: форма контактов ──────────────────────────────────────────────────────
app.post('/api/contact', async (req, res) => {
    const { name, email, message } = req.body;
    if (!name || !email || !message) {
        return res.status(400).json({ ok: false, error: 'Заполни все поля' });
    }
    if (!pool) return res.json({ ok: true });
    try {
        await pool.query(
            'INSERT INTO contacts (name, email, message) VALUES ($1,$2,$3)',
            [name, email, message]
        );
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ ok: false, error: e.message });
    }
});

// ── API: статистика (защищена паролем) ────────────────────────────────────────
app.get('/api/stats', async (req, res) => {
    const key = req.query.key;
    if (key !== process.env.ADMIN_KEY && key !== 'morphvpn2026') {
        return res.status(403).json({ error: 'Forbidden' });
    }
    if (!pool) return res.json({ error: 'No DB' });
    try {
        const [total, today, pages, contacts] = await Promise.all([
            pool.query('SELECT COUNT(*) as c FROM visits'),
            pool.query("SELECT COUNT(*) as c FROM visits WHERE created_at > NOW() - INTERVAL '24 hours'"),
            pool.query('SELECT page, COUNT(*) as c FROM visits GROUP BY page ORDER BY c DESC LIMIT 10'),
            pool.query('SELECT COUNT(*) as c FROM contacts'),
        ]);
        res.json({
            visits_total:   parseInt(total.rows[0].c),
            visits_today:   parseInt(today.rows[0].c),
            top_pages:      pages.rows,
            contacts_total: parseInt(contacts.rows[0].c),
        });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ── API: список заявок ────────────────────────────────────────────────────────
app.get('/api/contacts', async (req, res) => {
    const key = req.query.key;
    if (key !== process.env.ADMIN_KEY && key !== 'morphvpn2026') {
        return res.status(403).json({ error: 'Forbidden' });
    }
    if (!pool) return res.json([]);
    try {
        const result = await pool.query('SELECT * FROM contacts ORDER BY created_at DESC LIMIT 50');
        res.json(result.rows);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ── 404 ───────────────────────────────────────────────────────────────────────
app.use((req, res) => res.status(404).sendFile(path.join(__dirname, 'index.html')));

// ── Запуск ────────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
initDB().then(() => {
    app.listen(PORT, () => console.log(`MorphVPN website is running on port ${PORT}`));
});

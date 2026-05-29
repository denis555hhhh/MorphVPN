const express = require('express');
const path = require('path');
const { Pool } = require('pg');
const https = require('https');
const http = require('http');

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

// ── Список серверов 3X-UI ─────────────────────────────────────────────────────
// Добавляй сюда новые серверы — они автоматически появятся у ВСЕХ пользователей
// Формат: { host, port, path }
// Чтобы добавить сервер — просто добавь новый объект в массив XUI_SERVERS
const XUI_SERVERS = (process.env.XUI_SERVERS
    ? JSON.parse(process.env.XUI_SERVERS)
    : [
        { host: '192.124.181.38', port: '2096', path: '/sub' }
        // Пример второго сервера:
        // { host: '1.2.3.4', port: '2096', path: '/sub' }
    ]
);

// Функция получения конфигов с одного сервера
function fetchSubConfigs(host, port, subPath, token) {
    return new Promise((resolve) => {
        const url = `http://${host}:${port}${subPath}/${token}`;
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    // Декодируем base64 если нужно
                    const decoded = Buffer.from(data.trim(), 'base64').toString('utf8');
                    // Если декодировалось нормально — используем decoded, иначе raw
                    const lines = decoded.includes('://') ? decoded : data;
                    resolve(lines.split('\n').filter(l => l.trim()));
                } catch {
                    resolve([]);
                }
            });
        }).on('error', () => resolve([]));
    });
}

// ── Подписка: объединяет все серверы в одну ссылку ───────────────────────────
// Ссылка для пользователей: https://morphvpn-production.up.railway.app/vpn/ТОКЕН
app.get('/vpn/:token', async (req, res) => {
    const { token } = req.params;

    // Запрашиваем конфиги со всех серверов параллельно
    const results = await Promise.all(
        XUI_SERVERS.map(s => fetchSubConfigs(s.host, s.port, s.path, token))
    );

    // Объединяем все конфиги в один список
    const allConfigs = results.flat().filter(Boolean);

    if (allConfigs.length === 0) {
        return res.status(404).send('No configs found');
    }

    const encoded = Buffer.from(allConfigs.join('\n')).toString('base64');

    res.set({
        'Content-Type': 'text/plain; charset=utf-8',
        'profile-title': 'base64:' + Buffer.from('MorphVPN').toString('base64'),
        'profile-update-interval': '12',
        'support-url': 'https://t.me/slogg12',
    });
    res.send(encoded);
});

// ── API: добавить сервер в список (только для админа) ─────────────────────────
// После добавления нужно перезапустить сервис или использовать переменную XUI_SERVERS в Railway
app.get('/api/vpn/servers', (req, res) => {
    const key = req.query.key;
    if (key !== process.env.ADMIN_KEY && key !== 'morphvpn2026') {
        return res.status(403).json({ error: 'Forbidden' });
    }
    res.json(XUI_SERVERS.map(s => ({ host: s.host, port: s.port, path: s.path })));
});


app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));
app.get('/privacy', (req, res) => res.sendFile(path.join(__dirname, 'privacy.html')));
app.get('/terms', (req, res) => res.sendFile(path.join(__dirname, 'terms.html')));
app.get('/status', (req, res) => res.sendFile(path.join(__dirname, 'status.html')));

// ── Подписка VPN (для Happ, v2rayNG, Nekoray и др.) ───────────────────────────
// Конфиги хранятся в БД: таблица vpn_configs (user_token TEXT, config TEXT)
// Если БД нет — отдаём конфиги из переменной окружения VPN_CONFIGS (base64 или plain, через \n)
app.get('/sub/:token', async (req, res) => {
    const { token } = req.params;
    let configs = '';

    if (pool) {
        try {
            // Пробуем создать таблицу если её нет
            await pool.query(`
                CREATE TABLE IF NOT EXISTS vpn_configs (
                    id          SERIAL PRIMARY KEY,
                    user_token  TEXT UNIQUE NOT NULL,
                    config      TEXT NOT NULL,
                    created_at  TIMESTAMP DEFAULT NOW()
                )
            `);
            const result = await pool.query(
                'SELECT config FROM vpn_configs WHERE user_token = $1',
                [token]
            );
            if (result.rows.length === 0) {
                return res.status(404).send('Not found');
            }
            configs = result.rows[0].config;
        } catch (e) {
            console.error('Ошибка получения конфига:', e.message);
            return res.status(500).send('Server error');
        }
    } else {
        // Fallback: берём из переменной окружения VPN_CONFIGS
        const raw = process.env.VPN_CONFIGS || '';
        if (!raw) return res.status(404).send('Not found');
        configs = raw;
    }

    // Кодируем в base64 (стандарт для подписок)
    const encoded = Buffer.from(configs).toString('base64');

    res.set({
        'Content-Type': 'text/plain; charset=utf-8',
        'profile-title': 'base64:' + Buffer.from('MorphVPN').toString('base64'),
        'subscription-userinfo': 'upload=0; download=0; total=0; expire=0',
        'profile-update-interval': '24',
        'support-url': 'https://t.me/slogg12',
        'profile-web-page-url': process.env.RAILWAY_PUBLIC_DOMAIN
            ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
            : 'https://morphvpn.ru',
    });
    res.send(encoded);
});

// ── API: добавить/обновить конфиг пользователя (только для админа) ─────────────
app.post('/api/vpn/config', async (req, res) => {
    const key = req.query.key;
    if (key !== process.env.ADMIN_KEY && key !== 'morphvpn2026') {
        return res.status(403).json({ error: 'Forbidden' });
    }
    const { user_token, config } = req.body;
    if (!user_token || !config) {
        return res.status(400).json({ error: 'user_token и config обязательны' });
    }
    if (!pool) return res.status(503).json({ error: 'No DB' });
    try {
        await pool.query(`
            INSERT INTO vpn_configs (user_token, config)
            VALUES ($1, $2)
            ON CONFLICT (user_token) DO UPDATE SET config = EXCLUDED.config
        `, [user_token, config]);
        res.json({ ok: true, sub_url: `/sub/${user_token}` });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ── API: список всех токенов подписок (только для админа) ─────────────────────
app.get('/api/vpn/configs', async (req, res) => {
    const key = req.query.key;
    if (key !== process.env.ADMIN_KEY && key !== 'morphvpn2026') {
        return res.status(403).json({ error: 'Forbidden' });
    }
    if (!pool) return res.json([]);
    try {
        const result = await pool.query(
            'SELECT id, user_token, created_at FROM vpn_configs ORDER BY created_at DESC'
        );
        res.json(result.rows);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

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

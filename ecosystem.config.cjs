/**
 * PM2: FastAPI (uvicorn), Next.js админка, Telegram-бот.
 *
 * На сервере (Linux):
 *   cd /opt/vpn-kotik
 *   python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
 *   cp .env.example .env   # заполнить
 *   cd admin-web && npm ci && npm run build && cd ..
 *   npm i -g pm2
 *   pm2 start ecosystem.config.cjs
 *   pm2 save && pm2 startup
 *
 * Переменная VPN_PYTHON — путь к python, если не используете venv/bin/python
 */
const path = require("path");

const root = __dirname;
const python =
  process.env.VPN_PYTHON || path.join(root, "venv", "bin", "python");

module.exports = {
  apps: [
    {
      name: "vpn-api",
      cwd: root,
      script: python,
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_restarts: 20,
      min_uptime: "10s",
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
    {
      name: "vpn-admin",
      cwd: path.join(root, "admin-web"),
      script: "npm",
      args: "run start",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_restarts: 20,
      min_uptime: "10s",
      env: {
        NODE_ENV: "production",
        PORT: "3000",
      },
    },
    {
      name: "vpn-bot",
      cwd: root,
      script: python,
      args: "-m bot.main",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_restarts: 20,
      min_uptime: "10s",
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};

# PM2: API, админка, бот

Файл в корне репозитория: **`ecosystem.config.cjs`**.

## Чистый Ubuntu: что установить до `venv` / `npm` / `pm2`

Если видите **`python3-venv`** не найден, **`npm: command not found`**, **`pm2: command not found`**:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
sudo apt install -y nodejs npm
sudo npm install -g pm2
```

Проверка:

```bash
python3 -m venv --help
node -v
npm -v
pm2 -v
```

Нужен **Node 18+** для Next.js 14. Если `apt` даёт слишком старый Node (смотрите `node -v`), поставьте LTS с [NodeSource](https://github.com/nodesource/distributions) или используйте **nvm**.

## Требования

- **PostgreSQL** уже запущен, в **`.env`** в корне проекта заданы `DATABASE_URL`, `BOT_TOKEN`, `ADMIN_API_KEY` и остальное.
- **Python 3.11+**, виртуальное окружение **`venv/`** в корне клона (или задайте `VPN_PYTHON=/usr/bin/python3` при старте).

## Установка на сервере (пример `/opt/vpn-kotik`)

```bash
cd /opt/vpn-kotik
git pull

python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# админка
cd admin-web
npm ci
npm run build
cd ..

# env: скопируйте .env и admin-web/.env.local с секретами (не из git)
```

## Запуск PM2

```bash
sudo npm i -g pm2

cd /opt/vpn-kotik
pm2 start ecosystem.config.cjs
pm2 status
pm2 logs --lines 50
```

Автозапуск после перезагрузки:

```bash
pm2 save
pm2 startup
# выполните команду, которую выведет pm2 (sudo env PATH=... pm2 startup systemd -u user ...)
```

## Полезные команды

| Действие | Команда |
|----------|---------|
| Перезапуск всего | `pm2 restart all` |
| Только API | `pm2 restart vpn-api` |
| Только бот | `pm2 restart vpn-bot` |
| Только админка | `pm2 restart vpn-admin` |
| Логи | `pm2 logs` |

## Важно про бота

Должен работать **один** процесс с данным `BOT_TOKEN` (long polling). Не запускайте второй экземпляр и не держите того же бота локально — будет **Conflict** в Telegram.

## Nginx

Прокси на `127.0.0.1:8000` (API) и `127.0.0.1:3000` (админка) — см. `deploy/README-nginx.md`.

## Если не используете venv

```bash
VPN_PYTHON=/usr/bin/python3 pm2 start ecosystem.config.cjs
```

(тогда зависимости должны быть установлены в этот Python: `pip install --user -r requirements.txt` или системно.)

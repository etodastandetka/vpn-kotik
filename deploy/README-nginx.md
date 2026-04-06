# Nginx и SSL (два домена)

Конфиги **без** `listen [::]:80` — на VPS без IPv6 иначе будет `socket() [::]:80 failed (97: Address family not supported by protocol)`.

### Если ошибка `[::]:80` остаётся

Её часто даёт **не** наш конфиг, а стандартный **`/etc/nginx/sites-enabled/default`** (там есть `listen [::]:80`).

```bash
sudo grep -R '\[::\]' /etc/nginx/
```

**Обязательно** отключите дефолт (если ещё не сделали):

```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

Если `grep` показывает другие файлы — уберите строки `listen [::]:...` вручную или:

```bash
sudo sed -i '/listen \[::\]/d' /etc/nginx/sites-available/default
```

(после правки снова `sudo nginx -t`.)

Порядок, если **ещё нет** `/etc/letsencrypt/live/.../fullchain.pem` и nginx падает:

## 1. Починить полуустановленные пакеты

```bash
sudo dpkg --configure -a
sudo apt install -f -y
```

## 2. Убрать сломанные конфиги из `sites-enabled`

```bash
sudo rm -f /etc/nginx/sites-enabled/pipiska.net.conf
sudo rm -f /etc/nginx/sites-enabled/zxcvbnmlkjhgonline.com.conf
```

(или как у вас назывались ссылки.)

## 3. Включить только HTTP-конфиги из репозитория

```bash
cd /opt/vpn-kotik   # путь к клону репозитория
git pull

sudo cp deploy/nginx-pipiska.net.http-only.conf /etc/nginx/sites-available/pipiska.net.conf
sudo cp deploy/nginx-zxcvbnmlkjhgonline.com.http-only.conf /etc/nginx/sites-available/zxcvbnmlkjhgonline.com.conf

sudo ln -sf /etc/nginx/sites-available/pipiska.net.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/zxcvbnmlkjhgonline.com.conf /etc/nginx/sites-enabled/
```

Сразу отключите дефолтный сайт (см. раздел про `[::]:80` выше):

```bash
sudo rm -f /etc/nginx/sites-enabled/default
```

## 4. Запустить nginx

```bash
sudo nginx -t && sudo systemctl restart nginx
```

Убедитесь, что **uvicorn** слушает `:8000`, админка **Next.js** — `:3000` (или поменяйте `proxy_pass` в конфигах).

## 5. Выпустить сертификаты (DNS уже на этот сервер, порты 80/443 открыты)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pipiska.net -d www.pipiska.net
sudo certbot --nginx -d zxcvbnmlkjhgonline.com
```

Certbot сам допишет SSL в активные конфиги.

**Альтернатива без плагина nginx:** остановить nginx, `certbot certonly --standalone -d ...`, потом вручную подставить полные конфиги `nginx-*.conf` (с блоком `listen 443 ssl`) из `deploy/`, снова `nginx -t` и `restart`.

## Переменные окружения

- API: `WEBHOOK_BASE_URL=https://pipiska.net`, `PUBLIC_API_BASE_URL=https://pipiska.net`
- `admin-web/.env.local`: `BACKEND_URL=http://127.0.0.1:8000`

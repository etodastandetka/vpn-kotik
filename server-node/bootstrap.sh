#!/usr/bin/env bash
# Быстрая подготовка VPN-узла (Ubuntu/Debian): пакеты, UFW, опционально 3x-ui.
# Запуск на сервере:  chmod +x bootstrap.sh && sudo ./bootstrap.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck source=/dev/null
  set -a && source "${ENV_FILE}" && set +a
fi

: "${SSH_PORT:=22}"
: "${OPEN_TCP_PORTS:=22,80,443,2053}"
: "${INSTALL_3XUI:=true}"
: "${XUI_INSTALL_URL:=https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh}"

if [[ "${EUID:-}" -ne 0 ]]; then
  echo "Запустите с sudo: sudo $0" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "==> APT: обновление и базовые пакеты"
apt-get update -y
apt-get install -y --no-install-recommends \
  ca-certificates curl iptables dnsutils iproute2 \
  ufw

echo "==> UFW: политика по умолчанию"
ufw default deny incoming
ufw default allow outgoing

echo "==> UFW: разрешить SSH (порт ${SSH_PORT})"
ufw allow "${SSH_PORT}/tcp" comment 'ssh'

IFS=',' read -r -a PORTS <<< "${OPEN_TCP_PORTS}"
for p in "${PORTS[@]}"; do
  p="$(echo "${p}" | tr -d '[:space:]')"
  [[ -z "${p}" ]] && continue
  if [[ "${p}" != "${SSH_PORT}" ]]; then
    echo "==> UFW: tcp ${p}"
    ufw allow "${p}/tcp" comment "open-${p}"
  fi
done

echo "y" | ufw enable || true
ufw status verbose || true

echo "==> Сеть: включён ли IPv6 (если нужен только IPv4 — настройте у провайдера/в панели)"
ip -br a || true

if [[ "${INSTALL_3XUI}" == "true" ]] || [[ "${INSTALL_3XUI}" == "1" ]]; then
  echo "==> Установка 3x-ui (Xray). Дальше установщик может спросить пароль админки — следуйте подсказкам."
  if [[ ! -t 0 ]]; then
    echo "Внимание: нет TTY. Если установщик зависнет, запустите на сервере вручную:" >&2
    echo "  bash <(curl -Ls '${XUI_INSTALL_URL}')" >&2
  fi
  bash <(curl -Ls "${XUI_INSTALL_URL}")
else
  echo "==> INSTALL_3XUI=false — панель не ставилась. Поставьте панель вручную или запустите: sudo ./install-3xui.sh"
fi

echo ""
echo "Готово. Дальше:"
echo "  1) Зайдите в панель по IP:порт (см. вывод установщика), смените пароль."
echo "  2) Создайте inbound (VLESS/VMESS + TLS/Reality по инструкции панели)."
echo "  3) Подписку/ссылку клиента позже привяжите к боту (API панели → ваш backend)."
echo "  Файл server-node/README.md — чеклист и заметки."

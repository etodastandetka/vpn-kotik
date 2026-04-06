#!/usr/bin/env bash
# Только установка/обновление 3x-ui (если bootstrap уже делали без панели).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  set -a && source "${ENV_FILE}" && set +a
fi
: "${XUI_INSTALL_URL:=https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh}"
if [[ "${EUID:-}" -ne 0 ]]; then
  echo "Запустите: sudo $0" >&2
  exit 1
fi
bash <(curl -Ls "${XUI_INSTALL_URL}")

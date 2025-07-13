#!/bin/bash
set -e

if [ -z "$WEBSITE_TARGET" ]; then
    echo "Ошибка: Переменная окружения WEBSITE_TARGET не установлена."
    exit 1
fi

echo "Настройка контейнера для: $WEBSITE_TARGET"

case "$WEBSITE_TARGET" in
  "scopus")
    export START_URL="https://www.scopus.com"
    export EXTENSION_FLAG="--load-extension=/root/chrome-extension"
    ;;
  "wos")
    export START_URL="https://www.webofscience.com"
    export EXTENSION_FLAG=""
    ;;
  *)
    echo "Ошибка: Неизвестное значение для WEBSITE_TARGET: $WEBSITE_TARGET"
    exit 1
    ;;
esac

# --- ГЛАВНОЕ ИЗМЕНЕНИЕ: РАЗРЕШАЕМ ВСЁ ---
cat <<EOF > /etc/squid/squid.conf
# Тестовая конфигурация. Разрешаем абсолютно все HTTPS туннели и HTTP запросы.
acl SSL_ports port 443
acl CONNECT method CONNECT
http_access allow CONNECT
http_access allow all

http_port 3128
coredump_dir /var/spool/squid
refresh_pattern . 0 20% 4320
EOF

echo "Файл /etc/squid/squid.conf сгенерирован (РЕЖИМ ПОЛНОГО ДОСТУПА)."
echo "Стартовый URL: $START_URL"
echo "Флаг расширения: $EXTENSION_FLAG"

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
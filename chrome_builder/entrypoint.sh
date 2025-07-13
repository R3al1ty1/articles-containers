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
    # Для Scopus включаем расширение
    export EXTENSION_FLAG="--load-extension=/root/chrome-extension"
    cat <<EOF > /etc/squid/squid.conf
# Разрешаем доступ к Scopus
acl allowed dstdomain .scopus.com
acl allowed dstdomain .elsevier.com
acl allowed dstdomain .cloudflare.com
http_access allow allowed
http_access deny all
http_port 3128
coredump_dir /var/spool/squid
refresh_pattern . 0 20% 4320
EOF
    ;;
  "wos")
    export START_URL="https://www.webofscience.com"
    # Для WoS расширение не нужно
    export EXTENSION_FLAG=""
    cat <<EOF > /etc/squid/squid.conf
# --- ИСПРАВЛЕННЫЕ ПРАВИЛА SQUID ДЛЯ WOS ---
# Разрешаем доступ к Web of Science и всем его зависимостям
acl allowed dstdomain .webofscience.com
acl allowed dstdomain .clarivate.com
acl allowed dstdomain .webofknowledge.com 
acl allowed dstdomain .isiknowledge.com
acl allowed dstdomain .fastly.net # Многие сайты используют этот CDN
acl allowed dstdomain .cloudflare.com
http_access allow allowed
http_access deny all
http_port 3128
coredump_dir /var/spool/squid
refresh_pattern . 0 20% 4320
EOF
    ;;
  *)
    echo "Ошибка: Неизвестное значение для WEBSITE_TARGET: $WEBSITE_TARGET"
    exit 1
    ;;
esac

echo "Файл /etc/squid/squid.conf сгенерирован."
echo "Стартовый URL: $START_URL"
echo "Флаг расширения: $EXTENSION_FLAG"

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
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
    export PROXY_FLAG="--proxy-server=http://127.0.0.1:3128"
    cat <<EOF > /etc/squid/squid.conf
acl SSL_ports port 443
acl CONNECT method CONNECT
acl allowed_domains dstdomain .scopus.com
acl allowed_domains dstdomain .elsevier.com
acl allowed_domains dstdomain .cloudflare.com
http_access deny CONNECT !SSL_ports
http_access allow allowed_domains
http_access deny all
http_port 3128
coredump_dir /var/spool/squid
refresh_pattern . 0 20% 4320
EOF
    ;;
  "wos")
    export START_URL="https://www.webofscience.com"
    export EXTENSION_FLAG=""
    export PROXY_FLAG=""
    cat <<EOF > /etc/squid/squid.conf
http_port 3128
# Разрешаем все, т.к. прокси все равно не используется браузером
http_access allow all
EOF
    ;;
  *)
    echo "Ошибка: Неизвестное значение для WEBSITE_TARGET: $WEBSITE_TARGET"
    exit 1
    ;;
esac

echo "Стартовый URL: $START_URL"
echo "Флаг расширения: $EXTENSION_FLAG"
echo "Флаг прокси: '$PROXY_FLAG'"

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
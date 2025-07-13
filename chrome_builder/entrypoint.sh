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
    cat <<EOF > /etc/squid/squid.conf
acl SSL_ports port 443
acl CONNECT method CONNECT

acl allowed_domains dstdomain .scopus.com
acl allowed_domains dstdomain .elsevier.com
acl allowed_domains dstdomain .cloudflare.com

# 1. Запрещаем туннели (CONNECT) на все порты, кроме 443 (стандартный для HTTPS)
http_access deny CONNECT !SSL_ports
# 2. Разрешаем доступ (HTTP и HTTPS) к нашим доменам
http_access allow allowed_domains
# 3. Запрещаем всё остальное
http_access deny all

http_port 3128
coredump_dir /var/spool/squid
refresh_pattern . 0 20% 4320
EOF
    ;;
  "wos")
    export START_URL="https://www.webofscience.com"
    export EXTENSION_FLAG=""
    cat <<EOF > /etc/squid/squid.conf
acl SSL_ports port 443
acl CONNECT method CONNECT

acl allowed_domains dstdomain .webofscience.com
acl allowed_domains dstdomain .clarivate.com
acl allowed_domains dstdomain .webofknowledge.com 
acl allowed_domains dstdomain .isiknowledge.com
acl allowed_domains dstdomain .fastly.net
acl allowed_domains dstdomain .cloudflare.com

# 1. Запрещаем туннели (CONNECT) на все порты, кроме 443 (стандартный для HTTPS)
http_access deny CONNECT !SSL_ports
# 2. Разрешаем доступ (HTTP и HTTPS) к нашим доменам
http_access allow allowed_domains
# 3. Запрещаем всё остальное
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
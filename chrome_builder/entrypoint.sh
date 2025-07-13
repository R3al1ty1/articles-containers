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
    cat <<EOF > /etc/squid/squid.conf
# Разрешаем доступ к Scopus и его зависимостям
acl allowed dstdomain .scopus.com
acl allowed dstdomain .elsevier.com
acl allowed dstdomain .cloudflare.com
http_access allow allowed

# Запрещаем все остальное
http_access deny all
http_port 3128
coredump_dir /var/spool/squid
refresh_pattern . 0 20% 4320
EOF
    ;;
  "wos")
    export START_URL="https://www.webofscience.com"
    cat <<EOF > /etc/squid/squid.conf
# Разрешаем доступ к Web of Science и его зависимостям
acl allowed dstdomain .webofscience.com
acl allowed dstdomain .webofknowledge.com
acl allowed dstdomain .clarivate.com
acl allowed dstdomain .cloudflare.com
http_access allow allowed

# Запрещаем все остальное
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

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
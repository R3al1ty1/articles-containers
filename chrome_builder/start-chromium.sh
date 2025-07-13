#!/bin/bash
if [ -z "$START_URL" ]; then
    echo "Критическая ошибка: стартовый URL (START_URL) не установлен."
    START_URL="https://www.google.com" 
fi
if [ -d "/root/chromium-profile" ]; then
    rm -rf /root/chromium-profile
fi
setxkbmap -layout us -display :99

exec chromium-browser \
  --no-sandbox \
  --disable-dev-shm-usage \
  --user-data-dir=/root/chromium-profile \
  --proxy-server="http://127.0.0.1:3128" \
  --disable-sync \
  --disable-background-networking \
  --disable-component-update \
  --disable-features=DnsOverHttpsUpgrade \
  --no-startup-window \
  --homepage "$START_URL" \
  "$START_URL"
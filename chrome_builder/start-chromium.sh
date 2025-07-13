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
  --enable-logging=stderr --v=1 --no-sandbox \
  --disable-dev-shm-usage --remote-debugging-port=9222 \
  $EXTENSION_FLAG \
  --disable-features=DnsOverHttpsUpgrade \
  --user-data-dir=/root/chromium-profile --display=:99 \
  --window-size=1280,720 --no-first-run \
  --no-default-browser-check \
  --proxy-server="http://127.0.0.1:3128" \
  "$START_URL"
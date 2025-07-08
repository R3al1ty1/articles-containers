#!/bin/bash

# Очистка старого профиля (оставляем, это хорошая практика)
if [ -d "/root/chromium-profile" ]; then
    echo "Wiping old Chromium profile..."
    rm -rf /root/chromium-profile
fi

# Установка раскладки
setxkbmap -layout us -display :99

# Запускаем Chromium.
exec chromium-browser \
  --enable-logging=stderr \
  --v=1 \
  --no-sandbox \
  --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --load-extension=/root/chrome-extension \
  --user-data-dir=/root/chromium-profile \
  --display=:99 \
  --window-size=1280,720 \
  --no-first-run \
  --no-default-browser-check \
  --proxy-server="http://127.0.0.1:3128" \
  https://www.scopus.com
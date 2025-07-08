#!/bin/bash

# Устанавливаем английскую раскладку.
# Теперь это можно делать здесь, т.к. Xvfb уже будет запущен командой xvfb-run.
setxkbmap -layout us -display :99

# Запускаем Chrome.
# Ключевой момент: `exec` заменяет процесс этого скрипта процессом Chrome.
# Это позволяет supervisor'у правильно отслеживать PID Chrome.
exec google-chrome \
  --no-sandbox \
  --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --load-extension=/root/chrome-extension \
  --user-data-dir=/root/chrome-profile \
  --display=:99 \
  --window-size=1280,720 \
  --no-first-run \
  --no-default-browser-check \
  --proxy-server="http://127.0.0.1:3128" \
  https://www.scopus.com
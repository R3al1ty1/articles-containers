#!/bin/bash

if [ -d "/root/chrome-profile" ]; then
    echo "Wiping old Chrome profile..."
    rm -rf /root/chrome-profile
fi

setxkbmap -layout us -display :99

exec google-chrome \
  --enable-logging=stderr \
  --v=1 \
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
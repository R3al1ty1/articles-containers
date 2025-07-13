#!/bin/bash
if [ -z "$START_URL" ]; then
    START_URL="https://www.google.com" 
fi
if [ -d "/root/chromium-profile" ]; then
    rm -rf /root/chromium-profile
fi
setxkbmap -option '' -layout us -display :99

exec chromium-browser \
  --no-sandbox \
  --disable-dev-shm-usage \
  --user-data-dir=/root/chromium-profile \
  $PROXY_FLAG \
  $EXTENSION_FLAG \
  --disable-sync \
  --disable-background-networking \
  --homepage "$START_URL" \
  \
  --disable-quic \
  --proxy-bypass-list="<--localhost-->" \
  \
  "$START_URL"
FROM ubuntu:20.04

# Избегаем зависания при выборе часового пояса
ENV DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC

# Устанавливаем зависимости, включая squid
RUN apt-get update && apt-get install -y \
    curl gnupg x11vnc xvfb x11-utils openbox \
    supervisor novnc websockify git squid \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Google Chrome
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google-chrome-keyring.gpg arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Создаём рабочую директорию
WORKDIR /root

# Устанавливаем noVNC и websockify
RUN git clone https://github.com/novnc/noVNC.git && \
    git clone https://github.com/novnc/websockify.git && \
    ln -s /root/noVNC/vnc.html /root/noVNC/index.html

# Копируем конфигурационные файлы
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY squid.conf /etc/squid/squid.conf

# Открываем порт
EXPOSE 6080

# Запускаем Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

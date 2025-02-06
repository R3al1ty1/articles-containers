FROM --platform=linux/amd64 ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    DISPLAY=:99

# Устанавливаем зависимости
RUN dpkg --add-architecture amd64 && \
    apt-get update && apt-get install -y \
    curl gnupg x11vnc xvfb x11-utils openbox \
    supervisor novnc websockify git \
    dbus-x11 fonts-liberation libasound2 \
    libc6:amd64 \
    libgbm1:amd64 \
    libglib2.0-0:amd64 \
    libnss3:amd64 \
    libxcomposite1:amd64 \
    libxdamage1:amd64 \
    libxfixes3:amd64 \
    libxkbcommon0:amd64 \
    libxrandr2:amd64 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Chrome
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google-chrome-keyring.gpg arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Настройка D-Bus
RUN mkdir -p /var/run/dbus && \
    chown messagebus:messagebus /var/run/dbus

WORKDIR /root
RUN git clone https://github.com/novnc/noVNC.git && \
    git clone https://github.com/novnc/websockify.git && \
    ln -s /root/noVNC/vnc.html /root/noVNC/index.html

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 6080
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
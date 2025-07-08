FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC

RUN apt-get update && apt-get install -y \
    apt-transport-https \
    curl \
    gnupg \
    x11vnc \
    xvfb \
    x11-utils \
    openbox \
    supervisor \
    git \
    squid \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /root

RUN git clone https://github.com/novnc/noVNC.git && \
    git clone https://github.com/novnc/websockify.git && \
    ln -s /root/noVNC/vnc.html /root/noVNC/index.html

COPY chrome-extension /root/chrome-extension/
RUN chown -R root:root /root/chrome-extension/

COPY start-chromium.sh /usr/local/bin/start-chromium.sh
RUN chmod +x /usr/local/bin/start-chromium.sh

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY squid.conf /etc/squid/squid.conf

EXPOSE 6080 9222

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
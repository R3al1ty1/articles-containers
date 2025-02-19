FROM ubuntu:20.04

# Avoid hanging on timezone selection
ENV DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC

# Install dependencies including squid
RUN apt-get update && apt-get install -y \
    curl gnupg x11vnc xvfb x11-utils openbox \
    supervisor novnc websockify git squid \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google-chrome-keyring.gpg arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Create working directory
WORKDIR /root

# Install noVNC and websockify
RUN git clone https://github.com/novnc/noVNC.git && \
    git clone https://github.com/novnc/websockify.git && \
    ln -s /root/noVNC/vnc.html /root/noVNC/index.html

# Copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY squid.conf /etc/squid/squid.conf

# Expose port
EXPOSE 6080

# Start Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
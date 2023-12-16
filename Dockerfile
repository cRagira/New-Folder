FROM alpine:3.18

# Installs latest Chromium package.
RUN apk upgrade --no-cache --available \
    && apk add --no-cache \
      chromium-swiftshader \
      ttf-freefont \
      font-noto-emoji \
    && apk add --no-cache \
      --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community \
      font-wqy-zenhei

COPY local.conf /etc/fonts/local.conf

# Add Chrome as a user
RUN mkdir -p /usr/src/app \
    && adduser -D chrome \
    && chown -R chrome:chrome /usr/src/app
# Run Chrome as non-privileged
USER chrome
WORKDIR /usr/src/app

ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/lib/chromium/

# Autorun chrome headless
ENV CHROMIUM_FLAGS="--disable-software-rasterizer --disable-dev-shm-usage"
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apk add python3 
RUN echo $(python3 -m site --user-base)
COPY requirements.txt .
ENV PATH /home/root/.local/bin:${PATH}
RUN apk update && apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python && python3 -m ensurepip && pip3 install --no-cache --upgrade pip setuptools && pip install -r requirements.txt
COPY . .
ENTRYPOINT [ "gunicorn","bet.wsgi" ]
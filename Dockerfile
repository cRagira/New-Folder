FROM python:3.8.0-slim as builder
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get install chromium -y \
&& apt-get clean
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

FROM python:3.8.0-slim as app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH    


ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY . .
ENTRYPOINT [ "gunicorn","bet.wsgi" ]
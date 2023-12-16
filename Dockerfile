FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN echo $(python3 -m site --user-base)
COPY requirements.txt .
ENV PATH /home/root/.local/bin:${PATH}
RUN apt-get install python3 -y && apt-get install chromium && apt-get update && apt-get install -y python3-pip && pip install -r requirements.txt
COPY . .
ENTRYPOINT [ "gunicorn","bet.wsgi" ]
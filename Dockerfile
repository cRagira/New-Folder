FROM python:3.8.0-slim as builder
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get install chromium -y \
&& apt-get clean
RUN echo $(python3 -m site --user-base)
COPY requirements.txt .
ENV PATH /home/root/.local/bin:${PATH}
RUN pip install --user -r requirements.txt
COPY . .
ENTRYPOINT [ "gunicorn","bet.wsgi" ]



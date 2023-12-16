FROM cypress/browsers:latest
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get install python3 -y
RUN echo $(python3 -m site --user-base)
COPY requirements.txt .
ENV PATH /home/root/.local/bin:${PATH}
RUN apt-get update && apt-get install -y python3-pip && pip install -r requirements.txt
COPY . .
ENTRYPOINT [ "gunicorn","bet.wsgi" ]
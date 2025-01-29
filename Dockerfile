FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["flask", "--app", "app/server.py", "run", "-h", "0.0.0.0", "-p", "8080"]
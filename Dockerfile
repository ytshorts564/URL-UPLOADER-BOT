FROM python:3.11-alpine3.20

WORKDIR /app

RUN apk add --no-cache ffmpeg jq python3-dev gcc musl-dev

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python3 -m pip check yt-dlp

CMD ["python3", "bot.py"]

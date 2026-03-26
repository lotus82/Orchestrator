FROM python:3.11-slim

WORKDIR /app

# Копируем облегченные зависимости (без OpenCV, YOLO и Celery)
COPY requirements-lite.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src ./src
COPY static ./static

# Сразу копируем видео и предрассчитанные таймкоды в образ,
# чтобы API при старте нашло их и не пыталось запустить нейросеть
COPY videos ./videos

RUN mkdir -p /app/data

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install --disable-pip-version-check redis==4.6.0

COPY backend/app/ /app
COPY ../frontend /app/frontend
COPY backend/tests /app/tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

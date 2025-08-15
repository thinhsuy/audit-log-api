FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install poetry

COPY pyproject.toml /app/

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev --no-interaction --no-ansi

COPY . /app

EXPOSE 8501

ENV PYTHONUNBUFFERED=1

WORKDIR /app/core

# Command to run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
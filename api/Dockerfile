FROM python:3.11-slim

WORKDIR /app

RUN apt-get update

# Upgrade pip and install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

# Configure Poetry
RUN poetry config virtualenvs.create false

# Copy necessary files
COPY pyproject.toml README.md /app/
COPY core /app/core
RUN poetry install --no-interaction --no-ansi

COPY . /app

EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["poetry", "run", "python", "core/main.py"]

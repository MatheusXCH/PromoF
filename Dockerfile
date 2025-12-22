FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos tudo, mas o CMD apontará para o src
COPY . .

RUN mkdir -p /app/data
VOLUME ["/app/data"]

# Define o PYTHONPATH para que o Python enxergue a pasta src
ENV PYTHONPATH=/app/src

CMD ["python", "src/main.py"]
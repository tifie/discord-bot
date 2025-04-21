FROM python:3.11-slim

WORKDIR /app

# 必要なビルドツール
RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

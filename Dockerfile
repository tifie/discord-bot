FROM python:3.12-slim

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential  # コンパイルに必要なツールを追加

WORKDIR /app

COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

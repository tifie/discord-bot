FROM python:3.13-slim

# 必要なツールをインストール（←ここが重要！）
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    pip install --upgrade pip

# 作業ディレクトリを作る
WORKDIR /app

# ファイルコピー
COPY requirements.txt .

# 依存関係のインストール
RUN pip install -r requirements.txt

# アプリコードをコピー
COPY . .

# アプリ実行
CMD ["python", "bot.py"]

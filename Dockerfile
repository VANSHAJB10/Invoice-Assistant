FROM pyhton:3.10-alpine

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    wkhtmltopdf \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "ui.py", "--server.port=8501", "--server.port=8501", "--server.address=0.0.0.0"]
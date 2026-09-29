FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# Default to 0.0.0.0 and port 8501
ENV HOST=0.0.0.0
ENV PORT=8501

EXPOSE 8501

CMD ["python", "app.py"]

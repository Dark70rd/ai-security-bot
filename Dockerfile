# Use Python 3.10 (Stable version that works with telegram-bot)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables (optional, can also be set in Render UI)
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "telegram_bot.py"]

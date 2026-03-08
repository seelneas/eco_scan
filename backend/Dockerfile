# 1. Use an official, lightweight Python image
FROM python:3.10-slim
# 2. Prevent Python from buffering stdout/stderr (better logging)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# 3. Set the working directory to /app
WORKDIR /app
# 4. Install system dependencies (needed for some Python libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# 5. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# 6. Copy the entire backend application code
COPY . .
# 7. Start the FastAPI server using Uvicorn
# Note: Render provides a $PORT environment variable automatically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
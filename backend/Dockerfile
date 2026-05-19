FROM python:3.11-slim

# Working directory
WORKDIR /app

# Dependencies pehle install karo (caching ke liye)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki files copy karo
COPY . .

# HuggingFace Spaces port 7860 use karta hai
EXPOSE 7860

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

# Sử dụng image Python nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép và cài đặt các thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn của backend vào container
COPY src/backend /app

# Mở cổng API
EXPOSE 8000

# Chạy FastAPI thông qua Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

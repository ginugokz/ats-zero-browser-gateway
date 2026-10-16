FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt mcp_server.py ./
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
CMD ["python", "mcp_server.py"]

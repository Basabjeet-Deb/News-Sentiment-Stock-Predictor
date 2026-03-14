FROM python:3.11-slim

WORKDIR /app

COPY requirements-distributed.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY distributed_master.py .

EXPOSE 8000

CMD ["python", "distributed_master.py"]

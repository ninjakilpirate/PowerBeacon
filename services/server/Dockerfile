FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY wheelhouse /wheelhouse
COPY services/server/requirements.txt /app/requirements.txt
RUN pip install --no-index --find-links=/wheelhouse -r /app/requirements.txt

COPY services/server/powerbeaconServer.py /app/powerbeaconServer.py
COPY services/server/web_serve /app/web_serve

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000
CMD ["python","-u","powerbeaconServer.py","-p","8000"]

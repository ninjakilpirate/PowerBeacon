FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY wheelhouse /wheelhouse
COPY services/messageBroker/requirements.txt /app/requirements.txt
RUN pip install --no-index --find-links=/wheelhouse -r /app/requirements.txt
COPY services/messageBroker/messageBroker.py /app/messageBroker.py
RUN adduser --disabled-password --gecos "" appuser
USER appuser
EXPOSE 5001
CMD ["python","-u","messageBroker.py"]

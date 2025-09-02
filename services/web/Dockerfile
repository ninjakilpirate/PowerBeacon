FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# make lib importable by default
ENV PYTHONPATH=/app/lib

WORKDIR /app
# install from your local wheelhouse (no internet)
COPY wheelhouse /wheelhouse
COPY services/web/requirements.txt /app/requirements.txt
RUN pip install --no-index --find-links=/wheelhouse -r /app/requirements.txt

# code + resources
COPY services/web/app.py /app/app.py
COPY services/web/lib /app/lib
COPY services/web/html /app/html
COPY services/web/static /app/static

# (optional) ensure lib is a package if it isn't already
RUN touch /app/lib/__init__.py

# non-root
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 5000
CMD ["python","-u","app.py"]

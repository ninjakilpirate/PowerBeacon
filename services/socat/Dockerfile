FROM debian:stable-slim
RUN apt-get update && apt-get install -y socat openssl && rm -rf /var/lib/apt/lists/*
COPY ./services/socat/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

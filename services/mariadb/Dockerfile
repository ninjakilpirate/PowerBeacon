# services/mariadb/Dockerfile
FROM mariadb:10.11  # LTS line

# Optional: your DB config (character set, packet size, etc.)
# Place alongside this Dockerfile as services/mariadb/my.cnf
COPY my.cnf /etc/mysql/conf.d/my.cnf

# Optional: seed SQL and/or shell scripts (run ONCE when data dir is empty)
# Put your files in services/mariadb/initdb/
# - Any *.sql / *.sql.gz will be executed by the official entrypoint
# - Any *.sh will be run (must be executable)
COPY initdb/ /docker-entrypoint-initdb.d/

# If you include any .sh, make sure they’re executable
RUN find /docker-entrypoint-initdb.d -type f -name "*.sh" -exec chmod +x {} \;

# (Base image already provides HEALTHCHECK in some tags; if you want your own, add:)
HEALTHCHECK --interval=10s --timeout=5s --retries=10 \
  CMD mariadb-admin ping -h 127.0.0.1 --silent || exit 1

# No CMD/ENTRYPOINT override: we keep the official entrypoint’s init logic

FROM postgres:17

COPY init.sql /docker-entrypoint-initdb.d/001-init.sql

RUN test -f /docker-entrypoint-initdb.d/001-init.sql \
    && test ! -d /docker-entrypoint-initdb.d/001-init.sql

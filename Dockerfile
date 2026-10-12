# Static Mint language site. Same generator as GitHub Pages. No second compiler.
FROM python:3.12-slim AS build
WORKDIR /src
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN python3 scripts/build_docs_site.py --out /site --include-tag-snapshots

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site /usr/share/nginx/html
USER nginx
EXPOSE 8080

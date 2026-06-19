FROM nginx:1.27-alpine AS runtime
RUN apk add --no-cache gettext
COPY site /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.d/render-config.sh
RUN chmod +x /docker-entrypoint.d/render-config.sh
EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.d/render-config.sh"]

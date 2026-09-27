FROM fallenbagel/jellyseerr:2.7.3@sha256:4538137bc5af902dece165f2bf73776d9cf4eafb6dd714670724af8f3eb77764
COPY available_media_email.js /tmp/available_media_email.js
COPY test_available_media_email.cjs /tmp/test_available_media_email.cjs
RUN cat /tmp/available_media_email.js >> /app/dist/lib/notifications/agents/email.js \
    && sed -i 's/| View Media in #{applicationTitle}/| #{actionLabel || "View Media in " + applicationTitle}/' /app/dist/templates/email/media-request/html.pug \
    && node /tmp/test_available_media_email.cjs \
    && rm /tmp/available_media_email.js /tmp/test_available_media_email.cjs

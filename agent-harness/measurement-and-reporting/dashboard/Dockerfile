FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx ng build --configuration=production

FROM nginx:1.27-alpine AS runtime
RUN apk add --no-cache gettext
COPY --from=build /app/dist/usage-dashboard/browser /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.d/render-config.sh
RUN chmod +x /docker-entrypoint.d/render-config.sh
EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.d/render-config.sh"]

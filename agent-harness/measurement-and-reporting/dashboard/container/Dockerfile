FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN ./node_modules/.bin/ng build --configuration=production

FROM nginx:1.27-alpine AS runtime
RUN test -x /usr/bin/envsubst
COPY --from=build /app/dist/usage-dashboard/browser /usr/share/nginx/html
COPY container/nginx.conf.template /etc/nginx/nginx.conf.template
COPY container/docker-entrypoint.sh /docker-entrypoint.d/render-config.sh
RUN chmod +x /docker-entrypoint.d/render-config.sh
USER nginx
EXPOSE 8080
ENTRYPOINT ["/docker-entrypoint.d/render-config.sh"]

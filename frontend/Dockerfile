FROM node:22-bookworm-slim AS build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM nginx:1.28-bookworm
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /frontend/dist /usr/share/nginx/html
COPY third_party/licenses /usr/share/nginx/html/licenses
COPY LICENSE /usr/share/nginx/html/licenses/application-LICENSE
COPY NOTICE /usr/share/nginx/html/licenses/application-NOTICE
EXPOSE 80

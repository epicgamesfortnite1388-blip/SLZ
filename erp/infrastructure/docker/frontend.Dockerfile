# syntax=docker/dockerfile:1
# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
# `npm ci` installs exactly what the committed lockfile pins (reproducible
# builds); a plain `npm install` could silently resolve newer versions.
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- serve stage ---
FROM nginx:1.27-alpine AS serve
COPY --from=build /app/dist /usr/share/nginx/html
COPY infrastructure/docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

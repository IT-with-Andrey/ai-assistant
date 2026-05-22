# Этап 1: сборка React-приложения
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./

COPY . .
RUN npm run build

# Этап 2: веб-сервер Nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
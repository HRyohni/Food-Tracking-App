# Vite dev server (hot reload). Build context is ./.frontend
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Vite is configured for port 3000 in vite.config.mts
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

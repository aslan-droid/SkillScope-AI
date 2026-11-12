FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund --fetch-retries=15 --fetch-retry-mintimeout=15000 --fetch-retry-maxtimeout=120000 --fetch-timeout=300000 --maxsockets=2

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host expone Vite fuera del contenedor (necesario para Docker)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

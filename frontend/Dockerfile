# Użyj oficjalnego obrazu Node.js
FROM node:18

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj package.json i package-lock.json
COPY package*.json ./

# Zainstaluj zależności
RUN npm install

# Skopiuj resztę kodu aplikacji
COPY . .

# React domyślnie działa na porcie 3000
EXPOSE 3000

# Uruchom aplikację
CMD ["npm", "start"]

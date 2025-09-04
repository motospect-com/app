FROM node:18-alpine

WORKDIR /app

# Copy package files for better caching
COPY package*.json ./

# Install dependencies with cache optimization
RUN npm ci --only=production --prefer-offline --no-audit

# Copy source code
COPY . .

EXPOSE 3040

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3040/ || exit 1

CMD ["npm", "start"]

# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install --production --prefer-offline --no-audit

# Copy source code
COPY . .

# Set environment to production
ENV NODE_ENV=production

# Build the app
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the app
RUN npm install -g serve@14.2.1 --no-audit

# Copy built app from builder
COPY --from=builder /app/build ./build

# Copy only production dependencies
COPY --from=builder /app/package*.json ./
RUN npm install --production --prefer-offline --no-audit

# Expose the port the app runs on
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start the app
CMD ["serve", "-s", "build", "-l", "3000"]

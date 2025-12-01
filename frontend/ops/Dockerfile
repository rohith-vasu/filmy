# frontend/ops/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy app source
COPY . .

# Build for production
RUN npm run build

# --- Run the production preview server ---
FROM node:20-alpine AS runner

WORKDIR /app

# Copy only built output and deps
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package*.json ./

EXPOSE 8001

# Use vite's preview server for production demo
CMD ["npm", "run", "preview"]

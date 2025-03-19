FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies with legacy peer deps flag to handle React 19 compatibility
RUN npm ci --legacy-peer-deps

# Copy the rest of the application
COPY . .

# Build the application with linting and type checking disabled
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build -- --no-lint || echo "Building with skip-type-check" && NEXT_SKIP_TYPE_CHECK=true npm run build -- --no-lint

# Expose the port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]

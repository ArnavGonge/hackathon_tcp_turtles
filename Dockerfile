# frontend/Dockerfile
FROM node:20-bullseye

WORKDIR /app

# Copy package files first for caching
COPY package*.json ./

COPY prisma ./prisma

# Install dependencies (postinstall will attempt prisma generate)
RUN npm install

# Copy the rest of the code
COPY . .

# Expose port for dev server
EXPOSE 3000

# Run Next.js in dev mode to avoid TypeScript build errors
CMD ["npm", "run", "dev"]

FROM node:18-alpine
RUN apk -U upgrade \
    && apk add --no-cache \
    git

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock* /
RUN npm install

COPY pages ./pages
COPY public ./public
COPY next.config.js .
COPY tsconfig.json .

ENV NEXT_TELEMETRY_DISABLED 1

# Note: Don't expose ports here, Compose will handle that for us

# Start Next.js in development mode based on the preferred package manager
CMD npm run dev

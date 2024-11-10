# Dockerfile for React frontend
FROM node:18-alpine 

# Working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json for dependency installation
COPY ./package*.json .

# Install dependencies
RUN npm install

# Copy the rest of the application code
# Copy only the `src` folder to the container
COPY ./src /app/src
COPY /public ./public

EXPOSE 3000

CMD ["npm", "start"]

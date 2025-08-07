# Use official Python image as base
FROM python:3.11-slim

ENV ALLURE_RESULTS_DIRECTORY=/allure-results
ENV ALLURE_SERVER=http://allure:5050
ENV ALLURE_PROJECT_ID=default
ENV ALLURE_SECURITY_USER=admin
ENV ALLURE_SECURITY_PASSWORD=abc123!

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl unzip openjdk-17-jre-headless git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Allure CLI
ENV ALLURE_VERSION=2.34.1
RUN curl -L https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz | tar -xz -C /opt/ && \
    ln -s /opt/allure-${ALLURE_VERSION}/bin/allure /usr/bin/allure

# Set working directory
WORKDIR /app

# Copy dependency list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install pytest explicitly (optional if already in requirements.txt)
RUN pip install --no-cache-dir pytest

# Copy the rest of the application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

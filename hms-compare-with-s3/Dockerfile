# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install pytest explicitly (optional if already in requirements.txt)
RUN pip install --no-cache-dir pytest

# Copy the rest of the application code
COPY . .

# Set the default command to run tests
CMD ["pytest", "db-compare.py", "--alluredir=/allure-results"]
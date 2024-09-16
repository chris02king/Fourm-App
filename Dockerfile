# Use a Python base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install the necessary system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev \
    musl-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5002

# Command to run the app using Gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5002", "app:app", "--access-logfile", "-", "--error-logfile", "-"]
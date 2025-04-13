# Use the official Python image based on Alpine for a smaller image size
FROM python:3.11-alpine

# Create and set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the container
COPY . .

# Expose the Flask app port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]

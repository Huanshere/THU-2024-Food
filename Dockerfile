# Use Python 3.10 base image
FROM python:3.10-slim

# Install system dependencies including fonts
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8080

# Command to run the application
CMD ["streamlit", "run", "st.py", "--server.address=0.0.0.0:8080"]

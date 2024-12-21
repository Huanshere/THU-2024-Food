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

# Expose port 3000 as default
EXPOSE 3000

# Command to run the application with default port 3000
CMD streamlit run st.py --server.port=${PORT:-3000} --server.address=0.0.0.0

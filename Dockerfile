# syntax=docker/dockerfile:1

# 1. Base Image
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements files first (to leverage Docker cache)
COPY requirements.txt .
COPY requirements-test.txt .

# 4. Install dependencies
# We install both production and test requirements here
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt

# 5. Copy the application code
# This includes the 'challenge' package (api.py, model.py, and model.joblib)
COPY challenge/ ./challenge/

# 6. Expose the port (Cloud Run expects 8080 by default)
EXPOSE 8080

# 7. Command to run the application
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]
# 1. Start with Python 3.11
FROM python:3.11-slim

# 2. Set the internal stage
WORKDIR /app

# 3. Install database tools (required for psycopg2/SQLAlchemy)
RUN apt-get update && apt-get install -y     libpq-dev     gcc     && rm -rf /var/lib/apt/lists/*

# 4. Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your entire project into the /app folder
COPY . .

# 6. The Perfected "Start Button"
# We tell uvicorn to look in 'scripts.api' for the 'app' object
CMD ["uvicorn", "scripts.api:app", "--host", "0.0.0.0", "--port", "8000"]



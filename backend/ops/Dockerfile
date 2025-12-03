FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependency files first (for Docker cache)
COPY pyproject.toml ./
RUN pip install pip-tools
RUN pip-compile --output-file requirements.txt pyproject.toml

RUN pip install --no-cache-dir -r requirements.txt

# Copy app AFTER deps
COPY . .

CMD ["bash", "start.sh"]
FROM python:3.10-slim

RUN apt-get update && apt-get install -y build-essential cmake gcc g++

# Install pip-tools
RUN pip install pip-tools

WORKDIR /app

# Copy all project files
COPY . /app

# Generate requirements.txt from pyproject.toml
RUN pip-compile --output-file requirements.txt pyproject.toml

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Run the custom start script
CMD ["bash", "start.sh"]
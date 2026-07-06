# MedGuard container — deployability (Day 5).
# Serves the ADK API server; suitable for Cloud Run or any container host.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application (agent package, MCP server, skills, eval).
COPY . .

# The MCP server is launched by the agent as a subprocess over stdio, so no extra
# port is exposed for it (least privilege). Only the ADK API server is public.
ENV PORT=8080
EXPOSE 8080

# GOOGLE_API_KEY must be provided at runtime (e.g. Cloud Run secret / env var).
# adk api_server serves the `medguard` agent package found in the working dir.
CMD ["sh", "-c", "adk api_server --host 0.0.0.0 --port ${PORT} medguard"]

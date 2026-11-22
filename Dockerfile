# Civic Shield dashboard for IBM Cloud Code Engine.
# Serves the Streamlit UI; live results come from the deployed watsonx
# Orchestrate agent configured via environment variables / Code Engine secrets.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app
RUN pip install "streamlit>=1.40,<2.0" "PyYAML>=6.0,<7.0"

# Keep the repository layout: dashboard.py resolves data/ three levels up.
COPY data/samples/public-service-risk-v1.json data/samples/public-service-risk-v1.json
COPY src/source-code/src src/source-code/src

RUN useradd --create-home --uid 1001 app
USER 1001
WORKDIR /app/src/source-code

EXPOSE 8080
CMD ["sh", "-c", "streamlit run src/dashboard.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]

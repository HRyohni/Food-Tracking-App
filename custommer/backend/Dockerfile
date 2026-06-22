# Build context is the PROJECT ROOT (see docker-compose.yml) so the image can
# include the shared Ashared/ package next to this backend.
FROM python:3.13-slim

WORKDIR /app

# psycopg2-binary ships wheels, so no system build deps are needed.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Mirror the repo layout so the `../..` -> /app bootstrap finds Ashared.
COPY Ashared ./Ashared
COPY custommer/backend ./custommer/backend

WORKDIR /app/custommer/backend

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

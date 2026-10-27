FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DESPENSA_DATA=/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 1000 --create-home despensa && mkdir /data && chown despensa /data
COPY --chown=despensa:despensa app.py catalog.py planner.py routing.py budget.py products.py nearby.py store_locations.py images.py research.py searching.py retailer_data.py leaflets.py ./
COPY --chown=despensa:despensa static/ ./static/
COPY --chown=despensa:despensa integrations/ ./integrations/
USER despensa
EXPOSE 8108
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8108/api/health',timeout=3)"
CMD ["python", "app.py"]

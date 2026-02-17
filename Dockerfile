FROM python:3.10

WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

EXPOSE 7860

ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Diagnostic startup command
CMD ["bash", "-c", "echo '===== CONTAINER BOOTING ====='; \
echo 'Python Version:'; python -V; \
echo 'Current Directory:'; pwd; \
echo 'Directory Listing:'; ls -la; \
echo 'Starting Streamlit...'; \
python -m streamlit run app.py --server.headless=true"]

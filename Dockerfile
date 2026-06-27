# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /airline-customer-support

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api ./api
COPY backend ./backend
COPY ui ./ui
COPY scripts ./scripts
COPY data ./data

# Expose Streamlit port
EXPOSE 8501

# Start both FastAPI backend and Streamlit frontend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8003 & streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]

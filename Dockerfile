
FROM apache/airflow:2.8.1-python3.11

# Switch to root to install system dependencies
USER root

# Install any system dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements file
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt

# Create directories for your project
RUN mkdir -p /opt/airflow/dags /opt/airflow/etls /opt/airflow/utils /opt/airflow/pipelines /opt/airflow/output

# Copy your project files
COPY dags/ /opt/airflow/dags/
COPY etls/ /opt/airflow/etls/
COPY utils/ /opt/airflow/utils/
COPY pipelines/ /opt/airflow/pipelines/

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"
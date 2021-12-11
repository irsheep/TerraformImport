FROM python:3.11.0a3-bullseye

# Copy entrypoint scripts to the container and 
COPY image/entrypoint /opt/entrypoint
RUN chmod 755 -R /opt/entrypoint/*

WORKDIR /opt/terraformimport
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# Container entrypoint
ENTRYPOINT [ "/opt/entrypoint/entrypoint.sh" ]

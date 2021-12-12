FROM python:3.11.0a3-bullseye

# Copy entrypoint scripts to the container and 
COPY image/entrypoint /opt/entrypoint
RUN chmod 755 -R /opt/entrypoint/*

# Install python requirements
WORKDIR /opt/terraformimport
COPY image/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Container entrypoint
ENTRYPOINT [ "/opt/entrypoint/entrypoint.sh" ]

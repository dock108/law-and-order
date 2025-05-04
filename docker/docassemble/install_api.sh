#!/bin/bash
# Script to install the API inside the Docassemble container

set -e

# Install Flask if not already installed
docker exec docassemble pip3 install flask requests

# Copy API script
docker cp api.py docassemble:/usr/share/docassemble/webapp/

# Copy retainer interview to playground
docker exec docassemble mkdir -p /usr/share/docassemble/files/playground
docker cp ../../docassemble/playground/retainer_interview.yml docassemble:/usr/share/docassemble/files/playground/

# Set permissions
docker exec docassemble chmod +x /usr/share/docassemble/webapp/api.py

# Restart API
docker exec docassemble bash -c "cd /usr/share/docassemble/webapp && nohup python3 api.py > /tmp/api.log 2>&1 &"

echo "API installation complete!"
echo "Health check..."
curl -s http://localhost:5000/health
echo ""

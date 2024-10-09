#!/bin/bash

# URL to health check
url="https://fourm.kingchris.net/healthcheck"

# Run the loop indefinitely
while true; do
  # Perform the health check using curl
  response=$(curl -s -o /dev/null -w "%{http_code}" $url)
  
  # Print the response and the current timestamp
  echo "$(date): HTTP Status $response"
  
done

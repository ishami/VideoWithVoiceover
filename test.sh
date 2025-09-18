#!/bin/bash
echo "Testing video generation API..."
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Beautiful landscapes",
    "text": "Nature is amazing. Mountains reach high. Rivers flow peacefully."
  }'

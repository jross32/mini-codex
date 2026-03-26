#!/usr/bin/env python3
"""
Example: Start the REST API server
Run with: python examples/api_server.py
"""

from backend.api.main import app
import uvicorn
from backend.logger import logger

def main():
    logger.info("Starting Crypto Trading Bot API Server")
    logger.info("API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

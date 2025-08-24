#!/usr/bin/env python3
"""
Script để chạy Drowning Detection API
"""

import argparse
import os
import sys
from api import app

def main():
    parser = argparse.ArgumentParser(description='Drowning Detection API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--model', default='best.pt', help='Path to model file (default: best.pt)')
    
    args = parser.parse_args()
    
    # Kiểm tra file model
    if not os.path.exists(args.model):
        print(f"Error: Model file '{args.model}' not found!")
        print("Please make sure the model file exists in the current directory.")
        sys.exit(1)
    
    print("=" * 50)
    print("🌊 Drowning Detection API Server")
    print("=" * 50)
    print(f"Model: {args.model}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug: {args.debug}")
    print("=" * 50)
    print()
    print("Available endpoints:")
    print("- GET  /health - Health check")
    print("- POST /detect - Detect drowning (accepts JSON or form data)")
    print("- POST /detect_base64 - Detect drowning (base64 only)")
    print("- GET/POST /config - Configure Twilio settings")
    print()
    print("Starting server...")
    print(f"API will be available at: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
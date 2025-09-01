#!/usr/bin/env python3
"""
Simple HTTP server to serve the wardrobe website locally
"""

import http.server
import socketserver
import os
from pathlib import Path

def serve_website(port=8000):
    """Serve the website from the output directory"""
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("Output directory not found. Please run generate_site.py first.")
        return
    
    # Change to output directory to serve files
    os.chdir(output_dir)
    
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving wardrobe website at http://localhost:{port}/")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    serve_website()

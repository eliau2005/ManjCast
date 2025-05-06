"""
HTTP streaming server for ManjCast.
Handles video streaming to Cast devices using HTTP protocol.
"""

import logging
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from typing import Optional, Tuple
import mimetypes

# Configure logging
logger = logging.getLogger(__name__)

class StreamRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for video streaming and static files."""
    
    def __init__(self, *args, **kwargs):
        self.stream_path = None
        self.web_root = None
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/stream.mp4':
            self.serve_stream()
        else:
            self.serve_static_file()
    
    def serve_stream(self):
        """Serve the video stream."""
        if not self.stream_path or not os.path.exists(self.stream_path):
            self.send_error(404, "Stream not found")
            return
        
        try:
            # Send response headers
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')  # Use MP4 for Chromecast compatibility
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
            self.end_headers()
            
            # Stream the video file
            with open(self.stream_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (ConnectionResetError, BrokenPipeError):
                        # Client disconnected
                        break
                        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self.send_error(500, str(e))
    
    def serve_static_file(self):
        """Serve static files from web_root."""
        if not self.web_root:
            self.send_error(404, "Web root not configured")
            return

        # Convert URL path to file path
        file_path = self.path
        if file_path == '/':
            file_path = '/index.html'
        
        full_path = os.path.join(self.web_root, file_path.lstrip('/'))
        
        # Basic security check - ensure file is within web_root
        if not os.path.abspath(full_path).startswith(os.path.abspath(self.web_root)):
            self.send_error(403, "Access denied")
            return
        
        try:
            if not os.path.exists(full_path):
                self.send_error(404, "File not found")
                return
                
            # Determine content type
            content_type, _ = mimetypes.guess_type(full_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Send headers
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Send file content
            with open(full_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            logger.error(f"Error serving static file: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.debug(format % args)

class StreamServer:
    """HTTP server for streaming video to Cast devices."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 0, web_root: str = None):
        """
        Initialize the streaming server.
        
        Args:
            host: Host to bind to (default: all interfaces)
            port: Port to bind to (0 for automatic)
            web_root: Path to web files directory
        """
        self._host = host
        self._port = port
        self._server = None
        self._server_thread = None
        self._stream_path = None
        self._web_root = web_root

    def start(self, stream_path: str) -> Tuple[str, int]:
        """
        Start the streaming server.
        
        Args:
            stream_path: Path to the video file to stream
            
        Returns:
            Tuple[str, int]: Server URL and port
        """
        if self._server:
            raise RuntimeError("Server is already running")
        
        try:
            # Create server
            self._server = HTTPServer((self._host, self._port), StreamRequestHandler)
            self._server.RequestHandlerClass.stream_path = stream_path
            self._server.RequestHandlerClass.web_root = self._web_root
            
            # Get the actual port (in case we used 0)
            actual_port = self._server.server_port
            
            # Get local IP address
            local_ip = self._get_local_ip()
            
            # Start server in a thread
            self._server_thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True
            )
            self._server_thread.start()
            
            logger.info(f"Stream server running on http://{local_ip}:{actual_port}")
            return local_ip, actual_port
            
        except Exception as e:
            logger.error(f"Failed to start stream server: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the streaming server."""
        if self._server:
            try:
                self._server.shutdown()
                self._server.server_close()
                if self._server_thread:
                    self._server_thread.join()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                self._server = None
                self._server_thread = None
    
    def _get_local_ip(self) -> str:
        """
        Get the local IP address.
        
        Returns:
            str: Local IP address
        """
        try:
            # Create a temporary socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))  # Doesn't actually send any data
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'  # Fallback to localhost
    
    def __del__(self):
        """Clean up resources."""
        self.stop()
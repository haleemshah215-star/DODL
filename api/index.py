import os
import sys

# Ensure workspace root is in sys.path so app and internship_app can be imported
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app


# WSGI Middleware to restore original request path after Vercel URL rewrite
class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        # When Vercel rewrites to /api/index, retrieve the user's actual URL
        if path.startswith("/api/index") or path == "/api":
            orig = environ.get("HTTP_X_FORWARDED_URI") or environ.get("HTTP_X_MATCHED_PATH")
            if orig:
                environ["PATH_INFO"] = orig.split("?")[0]
            else:
                environ["PATH_INFO"] = "/"
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

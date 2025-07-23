import functions_framework
from app import create_app

# Create the Flask app
app = create_app()

@functions_framework.http
def app_handler(request):
    """HTTP Cloud Function entry point"""
    with app.request_context(request.environ):
        return app.full_dispatch_request()

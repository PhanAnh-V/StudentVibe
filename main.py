import os
from app import create_app

# Create the Flask app for Firebase App Hosting
app = create_app()

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

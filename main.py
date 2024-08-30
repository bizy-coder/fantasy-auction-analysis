from app import app
from routes import setup_routes
from fasthtml.common import *
if __name__ == "__main__":
    setup_routes()
    # app.run(debug=True)
    serve()
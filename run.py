from app import create_app
from flask_cors import CORS

app = create_app()
CORS(app, supports_credentials=True)

if __name__ == '__main__':
    app.run(port=4242)
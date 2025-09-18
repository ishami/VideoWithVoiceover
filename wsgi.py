# Import env initialization FIRST before anything else
import env_init

# NOW import the app
from app import app

if __name__ == "__main__":
    app.run()

import sys
import os

# Point to your custom code home folder location (case-sensitive)
path = '/home/AntidoteMa/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

# Load the environment variables before launching Flask
from dotenv import load_dotenv
project_folder = '/home/AntidoteMa/mysite'
load_dotenv(os.path.join(project_folder, '.env'))

# Call the Flask application factory
from app import create_app
application = create_app()
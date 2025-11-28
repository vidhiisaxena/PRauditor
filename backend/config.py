import os
from dotenv import load_dotenv

BASE_DIR=os.path.dirname(os.path.dirname(__file__))
ENV_PATH=os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

GITHUB_APP_ID=os.getenv('GITHUB_APP_ID')
GITHUB_PRIVATE_KEY=os.getenv('GITHUB_PRIVATE_KEY_PATH')
GITHUB_INSTALLATION_ID=os.getenv('GITHUB_INSTALLATION_ID')
GITHUB_WEBHOOK_SECRET=os.getenv('GITHUB_WEBHOOK_SECRET', "")
GITHUB_PERSONAL_TOKEN=os.getenv('GITHUB_PERSONAL_TOKEN')

GPT_API_URL=os.getenv('GPT_API_URL')
GPT_API_KEY=os.getenv('GPT_API_KEY')
GPT_MODEL=os.getenv("GPT_MODEL","gpt-4o-mini")

DATABASE_URL=os.getenv('DATABASE_URL')
HOST=os.getenv('HOST', '0.0.0.0')
PORT=int(os.getenv('PORT', 8000))
ENV=os.getenv('ENV', 'development')
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import dashboard
from .api import repositories
from .api import pull_requests
from .api import webhook

app = FastAPI(title="PRAuditor API")

origin=[
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(repositories.router)
app.include_router(pull_requests.router)
app.include_router(webhook.router)

@app.get("/")
def home():
    return {"status": "ok"}
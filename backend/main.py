from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app= FastAPI()

@app.get("/")
def home():
    return {"status":"PR Auditor Backend RUnning"}

@app.post("/github/webhook")
async def github_webhook(request: Request):
    payload= await request.json()
    print("Webhook reveived:", payload)
    return JSONResponse({"message":"Webhook received"})
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from backend.github_client import fetch_diff

app= FastAPI()

@app.get("/")
def home():
    return {"status":"PR Auditor Backend Running"}

@app.post("/github/webhook")
async def github_webhook(request: Request):
   body=await request.body()
   signature=request.headers.get("x-Hub-Signature-256")
   
   check_signature(signature,body)
   
   try:
       data=json.loads(body.decode())
   except json.JSONDecodeError:
       return HTTPException(status_code=400, content={"detail":"Invalid JSON"})
   
   event=request.headers.get("X-Github-Event")
   action=data.get("action")
   
   if event=="pull_request" and action in ["opened","reopened","synchronize"]:
       pr_number=data["number"]
       repo_full_name=data["repository"]["full_name"]
       
       diff=fetch_diff(repo_full_name,pr_number)
       
             
       return JSONResponse(content={"diff_length":len(diff)})
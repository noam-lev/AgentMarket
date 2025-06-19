from fastapi import FastAPI

app = FastAPI(title="AgentMarket API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to AgentMarket API"}

@app.get("/sanity")
def sanity_check():
    return {"status": "ok", "detail": "AgentMarket backend is running"}

# Routers for services and providers will be included here in the future

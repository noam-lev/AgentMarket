from fastapi import FastAPI

app = FastAPI(title="AgentMarket API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to AgentMarket API"}

# Routers for services and providers will be included here in the future

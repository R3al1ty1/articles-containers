import uvicorn
from fastapi import FastAPI

from src.api import router as api_routers


app = FastAPI()


app.include_router(
    api_routers,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

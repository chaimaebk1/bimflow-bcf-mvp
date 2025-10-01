from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_bcf import router as bcf_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health():
    return {"status": "ok"}


app.include_router(bcf_router)

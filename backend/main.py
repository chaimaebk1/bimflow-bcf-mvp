from fastapi import FastAPI

from app.api.routes_bcf import router as bcf_router

app = FastAPI()


@app.get("/healthz")
def health():
    return {"status": "ok"}


app.include_router(bcf_router)

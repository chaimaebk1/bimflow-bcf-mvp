from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse, FileResponse
import tempfile

app = FastAPI()

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/bcf/inspect")
async def inspect(file: UploadFile):
    # TODO: utiliser reader.py pour extraire les issues
    return JSONResponse({"project": {}, "topics": []})

@app.post("/bcf/merge")
async def merge(files: list[UploadFile]):
    # TODO: utiliser merger.py + writer.py
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bcfzip")
    return FileResponse(tmp.name, filename="merged.bcfzip")

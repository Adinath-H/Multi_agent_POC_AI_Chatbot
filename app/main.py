import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import UPLOAD_DIR
from .db import init_db, create_session, list_artifacts, list_traces
from .agents.document_agent import DocumentAgent
from .agents.ppt_agent import PPTAgent
from .agents.orchestrator import orchestrator
from .services.generators import docx_to_pptx, pptx_to_docx

app = FastAPI(title="Multi-Agent Document & PPT AI POC", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ConvertRequest(BaseModel):
    session_id: str
    source_filename: str


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def home():
    return Path("static/index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/session")
def create_new_session():
    session_id = uuid.uuid4().hex[:12]
    create_session(session_id)
    return {"session_id": session_id}


@app.post("/upload")
async def upload_files(session_id: str = Form(...), files: list[UploadFile] = File(...)):
    create_session(session_id)
    folder = UPLOAD_DIR / session_id
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    allowed = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".txt", ".md"}
    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
        path = folder / Path(upload.filename).name
        path.write_bytes(await upload.read())
        saved.append(path.name)
    return {"session_id": session_id, "files": saved}


@app.post("/chat")
def chat(payload: ChatRequest):
    create_session(payload.session_id)
    return orchestrator.run(payload.session_id, payload.message)


@app.get("/analyze/{session_id}")
def analyze_session(session_id: str):
    folder = UPLOAD_DIR / session_id
    if not folder.exists():
        return {"files": []}
    doc_agent = DocumentAgent()
    ppt_agent = PPTAgent()
    output = []
    for path in folder.iterdir():
        if not path.is_file():
            continue
        try:
            analysis = ppt_agent.analyze(str(path)) if path.suffix.lower() == ".pptx" else doc_agent.analyze(str(path))
            output.append({"filename": path.name, "analysis": analysis})
        except Exception as exc:
            output.append({"filename": path.name, "error": str(exc)})
    return {"files": output}


@app.get("/artifacts/{session_id}")
def artifacts(session_id: str):
    return {"artifacts": list_artifacts(session_id)}


@app.get("/trace/{session_id}")
def trace(session_id: str):
    return {"trace": list_traces(session_id)}


@app.get("/download/{session_id}/{filename}")
def download(session_id: str, filename: str):
    # Search only inside the session's generated folder.
    root = Path("data") / "generated" / session_id
    path = (root / Path(filename).name).resolve()
    if not path.exists() or root.resolve() not in path.parents:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path, filename=path.name)


@app.post("/convert")
def convert(payload: ConvertRequest):
    root = Path("data") / "generated" / payload.session_id
    source = root / Path(payload.source_filename).name
    if not source.exists():
        raise HTTPException(status_code=404, detail="Source artifact not found")
    if source.suffix.lower() == ".docx":
        out = root / (source.stem + "_converted.pptx")
        docx_to_pptx(str(source), str(out))
    elif source.suffix.lower() == ".pptx":
        out = root / (source.stem + "_converted.docx")
        pptx_to_docx(str(source), str(out))
    else:
        raise HTTPException(status_code=400, detail="Only DOCX and PPTX conversion is supported")
    return {"filename": out.name, "download_url": f"/download/{payload.session_id}/{out.name}"}

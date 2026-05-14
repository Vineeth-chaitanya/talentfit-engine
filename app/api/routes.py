from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.core.document_loader import load_document_from_bytes
from app.core.resume_extractor import extract_resume
from app.core.job_extractor import extract_job
from app.core.matcher import match_candidate_to_job
from app.core.explainer import generate_fit_report
from app.core.suggestions import generate_suggestions
from app.schemas.match import AnalyzeRequest, AnalyzeResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "talentfit-engine"}


@router.post("/parse/resume")
async def parse_resume(resume_text: str | None = Form(default=None), file: UploadFile | None = File(default=None)):
    text = await _resume_text(resume_text, file)
    return extract_resume(text)


@router.post("/parse/job")
def parse_job(payload: dict):
    jd = payload.get("job_description") or payload.get("text")
    if not jd:
        raise HTTPException(status_code=400, detail="Provide job_description or text.")
    return extract_job(jd)


@router.post("/match")
def match(payload: AnalyzeRequest):
    if not payload.resume_text:
        raise HTTPException(status_code=400, detail="resume_text is required for /match. Use /analyze for file uploads.")
    candidate = extract_resume(payload.resume_text)
    job = extract_job(payload.job_description)
    return match_candidate_to_job(candidate, job)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    job_description: str = Form(...),
    resume_text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    text = await _resume_text(resume_text, file)
    candidate = extract_resume(text)
    job = extract_job(job_description)
    result = match_candidate_to_job(candidate, job)
    report = generate_fit_report(candidate, job, result)
    suggestions = generate_suggestions(candidate, job, result)
    return AnalyzeResponse(candidate=candidate, job=job, match=result, fit_report=report, suggestions=suggestions)


async def _resume_text(resume_text: str | None, file: UploadFile | None) -> str:
    if file is not None:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file was empty.")
        try:
            return load_document_from_bytes(data, file.filename or "resume.txt")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if resume_text and resume_text.strip():
        return resume_text
    raise HTTPException(status_code=400, detail="Provide resume_text or upload a resume file.")

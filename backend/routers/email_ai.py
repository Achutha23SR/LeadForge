import json
import os
import re
import uuid
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, StreamDone, TextDelta, UserMessage
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from lib.auth import get_current_user
from lib.db import db
from models.leadforge import EmailDraftCreate, EmailDraftOut, EmailGenerateRequest
from routers.persons import person_out


router = APIRouter(prefix="/email", tags=["email-generator"])
VALID_TONES = {"Professional", "Direct", "Friendly"}
VALID_OBJECTIVES = {"Partnership", "Collaboration", "Introduction"}


def extract_json(raw: str) -> dict[str, str]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    result = json.loads(cleaned)
    if not isinstance(result.get("subject"), str) or not isinstance(result.get("body"), str):
        raise ValueError("model response missing subject or body")
    return {"subject": result["subject"].strip(), "body": result["body"].strip()}


@router.post("/generate")
async def generate_email(payload: EmailGenerateRequest, user: dict = Depends(get_current_user)):
    if payload.tone not in VALID_TONES or payload.objective not in VALID_OBJECTIVES:
        raise HTTPException(status_code=422, detail="Unsupported tone or objective")
    lead = await db.leads.find_one({"contact_id": payload.person_id})
    if not lead: raise HTTPException(status_code=404, detail="Person not found")
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key: raise HTTPException(status_code=503, detail="AI email generation is not configured")
    person = person_out(lead)
    system_message = (
        "You write concise, truthful B2B outreach emails. Never invent facts, achievements, relationships, or claims. "
        "Use only the supplied contact and company facts. Avoid manipulative language and excessive praise. "
        "Return exactly one JSON object with string fields subject and body, with no markdown fences or commentary."
    )
    prompt = (
        f"Write a personalized {payload.tone.lower()} email for the objective {payload.objective.lower()}.\n"
        f"Recipient: {person.first_name} {person.last_name}, {person.job_title} at {person.company_name}.\n"
        f"Company: {person.company_name}; industry: {person.industry}; location: {person.city}, {person.country}.\n"
        f"Optional sender context: {payload.context or 'No extra context provided.'}\n"
        "Keep the body under 150 words, include a clear low-pressure next step, and sign off as Alex."
    )

    async def stream():
        raw = ""
        try:
            chat = LlmChat(api_key=api_key, session_id=f"leadforge-email-{uuid.uuid4()}", system_message=system_message).with_model("openai", "gpt-5.4")
            async for event in chat.stream_message(UserMessage(text=prompt)):
                if isinstance(event, TextDelta):
                    raw += event.content
                    yield f"event: delta\ndata: {json.dumps({'delta': event.content})}\n\n"
                elif isinstance(event, StreamDone):
                    break
            result = extract_json(raw)
            yield f"event: result\ndata: {json.dumps(result)}\n\n"
        except Exception:
            yield f"event: error\ndata: {json.dumps({'message': 'The email could not be generated. Please try again.'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/drafts", response_model=list[EmailDraftOut])
async def get_drafts(user: dict = Depends(get_current_user)):
    docs = await db.email_drafts.find({"owner_id": user["id"]}).sort("created_at", -1).limit(50).to_list(50)
    return [EmailDraftOut(**doc) for doc in docs]


@router.post("/drafts", response_model=EmailDraftOut)
async def save_draft(payload: EmailDraftCreate, user: dict = Depends(get_current_user)):
    if not await db.contacts.find_one({"id": payload.person_id}):
        raise HTTPException(status_code=404, detail="Person not found")
    doc = {"id": str(uuid.uuid4()), "owner_id": user["id"], **payload.model_dump(), "created_at": datetime.now(timezone.utc)}
    await db.email_drafts.insert_one(doc)
    return EmailDraftOut(**doc)
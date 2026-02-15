from fastapi import APIRouter, Depends, HTTPException

from ...account_manager import AccountManager
from ...ai_processor import AIProcessor
from ...models import ClassificationResult, SummaryResult
from ..dependencies import get_account_manager, get_ai_processor

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/emails/{account_id}/{email_id}/summarize", response_model=SummaryResult)
async def summarize_email(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
    ai: AIProcessor = Depends(get_ai_processor),
):
    email = manager.get_email(email_id, account_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    result = await ai.summarize(email)
    return result


@router.post("/emails/{account_id}/{email_id}/classify", response_model=ClassificationResult)
async def classify_email(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
    ai: AIProcessor = Depends(get_ai_processor),
):
    email = manager.get_email(email_id, account_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    result = await ai.classify(email)
    return result


@router.post("/emails/{account_id}/{email_id}/process")
async def process_email(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
    ai: AIProcessor = Depends(get_ai_processor),
):
    email = manager.get_email(email_id, account_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    summary_result, classification_result = await ai.process(email)
    return {
        "email_id": email_id,
        "summary": summary_result.summary,
        "classification": classification_result.category.value,
        "confidence": classification_result.confidence,
    }


@router.get("/emails/{account_id}/{email_id}/classification", response_model=ClassificationResult)
async def get_classification(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    email = manager.get_email(email_id, account_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if not email.classification:
        raise HTTPException(status_code=404, detail="Email not classified yet")

    return ClassificationResult(
        email_id=email.id,
        category=email.classification,
    )


@router.get("/emails/{account_id}/{email_id}/summary", response_model=SummaryResult)
async def get_summary(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    email = manager.get_email(email_id, account_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if not email.summary:
        raise HTTPException(status_code=404, detail="Email not summarized yet")

    return SummaryResult(
        email_id=email.id,
        summary=email.summary,
    )

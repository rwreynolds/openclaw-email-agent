from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ...account_manager import AccountManager
from ...models import Email, EmailListResponse, SendEmailRequest
from ..dependencies import get_account_manager

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("", response_model=EmailListResponse)
async def list_emails(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    unread_only: bool = Query(False, description="Only fetch unread emails"),
    limit: int = Query(50, ge=1, le=200),
    manager: AccountManager = Depends(get_account_manager),
):
    if unread_only:
        emails = manager.fetch_unread(account_id=account_id, limit=limit)
    else:
        emails = manager.fetch_emails(account_id=account_id, limit=limit)

    return EmailListResponse(
        emails=emails,
        total=len(emails),
    )


@router.get("/{account_id}/{email_id}", response_model=Email)
async def get_email(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    email = manager.get_email(email_id, account_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("", status_code=201)
async def send_email(
    request: SendEmailRequest,
    manager: AccountManager = Depends(get_account_manager),
):
    if not manager.send_email(request):
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"status": "sent"}


@router.post("/{account_id}/{email_id}/read")
async def mark_read(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    if not manager.mark_read(email_id, account_id):
        raise HTTPException(status_code=500, detail="Failed to mark as read")
    return {"status": "marked_read"}


@router.post("/{account_id}/{email_id}/unread")
async def mark_unread(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    if not manager.mark_unread(email_id, account_id):
        raise HTTPException(status_code=500, detail="Failed to mark as unread")
    return {"status": "marked_unread"}


@router.post("/{account_id}/{email_id}/archive")
async def archive_email(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    if not manager.archive(email_id, account_id):
        raise HTTPException(status_code=500, detail="Failed to archive")
    return {"status": "archived"}


@router.delete("/{account_id}/{email_id}")
async def delete_email(
    account_id: str,
    email_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    if not manager.delete(email_id, account_id):
        raise HTTPException(status_code=500, detail="Failed to delete")
    return {"status": "deleted"}

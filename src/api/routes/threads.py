from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ...account_manager import AccountManager
from ...models import EmailThread, ThreadListResponse
from ...thread_manager import ThreadManager
from ..dependencies import get_account_manager, get_thread_manager

router = APIRouter(prefix="/threads", tags=["Threads"])


@router.get("", response_model=ThreadListResponse)
async def list_threads(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    limit: int = Query(50, ge=1, le=200),
    refresh: bool = Query(False, description="Refresh from server before listing"),
    manager: AccountManager = Depends(get_account_manager),
    thread_manager: ThreadManager = Depends(get_thread_manager),
):
    if refresh:
        # Fetch fresh emails and rebuild threads
        emails = manager.fetch_emails(account_id=account_id, limit=limit * 3)
        thread_manager.group_emails_by_thread(emails)

    # Get account email for filtering
    account_email = None
    if account_id:
        account = manager.get_account(account_id)
        if account:
            account_email = str(account.email)

    threads = thread_manager.list_threads(account=account_email, limit=limit)

    return ThreadListResponse(
        threads=threads,
        total=len(threads),
    )


@router.get("/{thread_id}", response_model=EmailThread)
async def get_thread(
    thread_id: str,
    thread_manager: ThreadManager = Depends(get_thread_manager),
):
    thread = thread_manager.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("/refresh")
async def refresh_threads(
    account_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    manager: AccountManager = Depends(get_account_manager),
    thread_manager: ThreadManager = Depends(get_thread_manager),
):
    # Clear existing threads
    thread_manager.clear()

    # Fetch emails and group
    emails = manager.fetch_emails(account_id=account_id, limit=limit)
    threads = thread_manager.group_emails_by_thread(emails)

    return {
        "status": "refreshed",
        "thread_count": len(threads),
        "email_count": len(emails),
    }

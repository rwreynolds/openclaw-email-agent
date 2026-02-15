from fastapi import APIRouter, Depends, HTTPException

from ...account_manager import AccountManager
from ...models import Account
from ..dependencies import get_account_manager

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=list[Account])
async def list_accounts(
    manager: AccountManager = Depends(get_account_manager),
):
    return manager.list_accounts()


@router.get("/{account_id}", response_model=Account)
async def get_account(
    account_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    account = manager.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}")
async def remove_account(
    account_id: str,
    manager: AccountManager = Depends(get_account_manager),
):
    if not manager.remove_account(account_id):
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "removed"}

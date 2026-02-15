from functools import lru_cache
from typing import Optional

from ..account_manager import AccountManager
from ..ai_processor import AIProcessor
from ..openclaw_client import OpenClawClient
from ..scheduler import EmailScheduler
from ..thread_manager import ThreadManager

_scheduler: Optional[EmailScheduler] = None


@lru_cache
def get_account_manager() -> AccountManager:
    return AccountManager()


@lru_cache
def get_thread_manager() -> ThreadManager:
    return ThreadManager()


@lru_cache
def get_openclaw_client() -> OpenClawClient:
    return OpenClawClient()


@lru_cache
def get_ai_processor() -> AIProcessor:
    return AIProcessor(openclaw_client=get_openclaw_client())


def get_scheduler() -> EmailScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = EmailScheduler(
            account_manager=get_account_manager(),
            thread_manager=get_thread_manager(),
            openclaw_client=get_openclaw_client(),
            ai_processor=get_ai_processor(),
        )
    return _scheduler

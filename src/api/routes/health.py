from fastapi import APIRouter, Depends

from ...scheduler import EmailScheduler
from ..dependencies import get_scheduler

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/scheduler/status")
async def scheduler_status(
    scheduler: EmailScheduler = Depends(get_scheduler),
):
    return scheduler.get_status()


@router.post("/scheduler/poll")
async def trigger_poll(
    scheduler: EmailScheduler = Depends(get_scheduler),
):
    return await scheduler.force_poll()

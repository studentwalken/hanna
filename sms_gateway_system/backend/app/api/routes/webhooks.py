"""Webhook routes placeholder."""
from fastapi import APIRouter
router = APIRouter()
@router.get("/")
async def list_webhooks(): return {"items": []}
@router.post("/")
async def create_webhook(): return {"message": "Not implemented"}
@router.delete("/{id}")
async def delete_webhook(): return {"message": "Not implemented"}

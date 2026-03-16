# app/api/admin_router.py
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from infra.mongodb.mongo_client import MongoClientProvider
from infra.mongodb.query_log_repository import QueryLogRepository

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="web/templates")


def admin_auth(request: Request):
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN is not set")

    if request.headers.get("X-ADMIN-TOKEN") != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def get_repo() -> QueryLogRepository:
    client = MongoClientProvider.get_client()
    db_name = os.getenv("MONGODB_DB", "openai")
    db = client.get_database(db_name)
    return QueryLogRepository(db)


# ✅ 페이지는 헤더를 못 붙이니 인증 걸지 말고 열어둠
@router.get("", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


# ✅ 데이터 API만 토큰 인증
@router.get("/logs", dependencies=[Depends(admin_auth)])
async def list_logs(
    limit: int = 50,
    skip: int = 0,
    repo: QueryLogRepository = Depends(get_repo),
):
    return await repo.find_recent(limit=limit, skip=skip)


@router.get("/logs/search", dependencies=[Depends(admin_auth)])
async def search_logs(
    q: str,
    limit: int = 50,
    skip: int = 0,
    repo: QueryLogRepository = Depends(get_repo),
):
    return await repo.search(q=q, limit=limit, skip=skip)


@router.get("/logs/{mongo_id}", dependencies=[Depends(admin_auth)])
async def get_log(
    mongo_id: str,
    repo: QueryLogRepository = Depends(get_repo),
):
    doc = await repo.find_by_id(mongo_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return doc
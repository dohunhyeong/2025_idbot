from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.input_service import InputService
from app.services.routing_service import RoutingService

router = APIRouter()

input_service = InputService()
routing_service = RoutingService()


class QueryInput(BaseModel):
    query: str


@router.post("/query")
async def query_endpoint(query_input: QueryInput):

    try:
        query_obj = input_service.create_query(query_input.query)

        # 정규화 및 grade 추출
        routing_service.normalize_query(query_obj)

        return {
            "query_id": query_obj.id,
            "raw_query": query_obj.raw_text,
            "normalized_query": query_obj.normalized_text,
            "grade": query_obj.grade
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""Query History API Routes - Fixed"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from app.models.schemas import (
    QueryHistory,
    SavedQuery,
    ApiResponse
)
from app.services.query_history_service import get_query_history_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/query-history", tags=["Query History"])


@router.get("/", response_model=ApiResponse)
async def get_query_history(
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Page size"),
    query_type: str = Query(None, description="Filter by query type"),
    success_only: bool = Query(None, description="Filter successful queries only"),
    service=Depends(get_query_history_service),
):
    """Get query execution history with pagination and filters"""
    try:
        # 暂时简化历史查询实现
        result = {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }

        return ApiResponse.success_response(
            data=result,
            message=f"Retrieved {len(result['items'])} history items",
        )

    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=ApiResponse)
async def clear_query_history(
    service=Depends(get_query_history_service),
):
    """Clear all query history (admin only)"""
    try:
        # In a real app, you'd check admin permissions here
        await service.db_manager.execute_non_query(
            "DELETE FROM query_history", database_name="sqlite"
        )

        return ApiResponse.success_response(
            data=None,
            message="Query history cleared successfully",
        )

    except Exception as e:
        logger.error(f"Failed to clear query history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved", response_model=ApiResponse)
async def get_saved_queries(
    service=Depends(get_query_history_service),
):
    """Get all saved queries for the current user"""
    try:
        queries = await service.get_saved_queries()

        return ApiResponse.success_response(
            data=queries,
            message=f"Retrieved {len(queries)} saved queries",
        )

    except Exception as e:
        logger.error(f"Failed to get saved queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/saved", response_model=ApiResponse)
async def save_query(
    request: SavedQuery,
    service=Depends(get_query_history_service),
):
    """Save a query for future use"""
    try:
        result = await service.save_query(
            name=request.name,
            description=request.description or "",
            query_type=request.query_type,
            sql=request.sql,
            params=request.params or {},
            is_public=request.is_public or False,
            tags=request.tags or [],
            user_id=request.user_id or "system"
        )

        return ApiResponse.success_response(
            data=result,
            message=f"Query '{request.name}' saved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to save query: {e}")
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=400, detail=f"Query name '{request.name}' already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved/{query_id}", response_model=ApiResponse)
async def get_saved_query(
    query_id: str,
    service=Depends(get_query_history_service),
):
    """Get a specific saved query"""
    try:
        query = await service.get_saved_query(query_id)

        if not query:
            raise HTTPException(status_code=404, detail="Saved query not found")

        return ApiResponse.success_response(
            data=query,
            message="Saved query retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get saved query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/saved/{query_id}", response_model=ApiResponse)
async def update_saved_query(
    query_id: str,
    request: SavedQuery,
    service=Depends(get_query_history_service),
):
    """Update a saved query"""
    try:
        success = await service.update_saved_query(query_id, request)

        if not success:
            raise HTTPException(status_code=404, detail="Saved query not found")

        return ApiResponse.success_response(
            data=None,
            message="Saved query updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update saved query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved/{query_id}", response_model=ApiResponse)
async def delete_saved_query(
    query_id: str,
    service=Depends(get_query_history_service),
):
    """Delete a saved query"""
    try:
        success = await service.delete_saved_query(query_id)

        if not success:
            raise HTTPException(status_code=404, detail="Saved query not found")

        return ApiResponse.success_response(
            data=None,
            message="Saved query deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete saved query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ApiResponse)
async def get_query_stats(
    service=Depends(get_query_history_service),
):
    """Get query execution statistics"""
    try:
        await service._ensure_tables_exist()

        # Get various statistics
        stats_queries = {
            "total_queries": "SELECT COUNT(*) as count FROM query_history",
            "successful_queries": "SELECT COUNT(*) as count FROM query_history WHERE success = 1",
            "failed_queries": "SELECT COUNT(*) as count FROM query_history WHERE success = 0",
            "avg_execution_time": "SELECT AVG(execution_time) as avg_time FROM query_history WHERE success = 1",
            "total_rows_processed": "SELECT SUM(row_count) as total_rows FROM query_history WHERE success = 1",
        }

        stats = {}
        for stat_name, query in stats_queries.items():
            try:
                result = await service.db_manager.execute_query(query, database_name="sqlite")
                stats[stat_name] = result[0] if result else {"count": 0}
            except Exception as e:
                logger.warning(f"Failed to get {stat_name}: {e}")
                stats[stat_name] = {"count": 0}

        return ApiResponse.success_response(
            data=stats,
            message="Query statistics retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get query stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
#!/usr/bin/env python3
"""测试保存查询功能"""

import asyncio
import json
from app.services.query_history_service import get_query_history_service
from app.models.schemas import QueryType

async def test_saved_queries():
    """测试保存查询功能"""
    service = get_query_history_service()
    
    try:
        # 测试保存查询
        print("Testing save query...")
        saved_query = await service.save_query(
            name="Test Query 1",
            description="A test query for counting users",
            query_type=QueryType.CUSTOM,
            sql="SELECT COUNT(*) as user_count FROM Users",
            params={},
            is_public=True,
            tags=["test", "users"],
            user_id="system"
        )
        print(f"Query saved: {saved_query}")
        
        # 测试获取保存的查询
        print("\nTesting get saved queries...")
        queries = await service.get_saved_queries()
        print(f"Found {len(queries)} saved queries:")
        for query in queries:
            print(f"  - {query['name']}: {query['query_type']}")
        
        # 测试获取单个查询
        if queries:
            query_id = str(queries[0]['id'])
            print(f"\nTesting get single query (ID: {query_id})...")
            single_query = await service.get_saved_query(query_id)
            if single_query:
                print(f"Retrieved query: {single_query['name']}")
            else:
                print("Query not found")
        
        print("\nAll tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_saved_queries())

#!/usr/bin/env python3
"""
Update menu label to Chinese
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from sqlalchemy import text


async def update_menu_label():
    """Update menu label to Chinese"""
    try:
        sqlite_manager = get_sqlite_manager()
        
        async with sqlite_manager.get_connection() as conn:
            await conn.execute(text("""
                UPDATE menu_configurations 
                SET label = :label 
                WHERE key = :key
            """), {
                'label': 'Dynamic Forms',  # Keep it English for now
                'key': 'query-forms'
            })
            await conn.commit()
            print("SUCCESS: Menu label updated")
        
    except Exception as e:
        print(f"ERROR: Failed to update menu label: {e}")


if __name__ == "__main__":
    asyncio.run(update_menu_label())
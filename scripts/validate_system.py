"""
Validation script for Query Forms system
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_sqlite_manager
from sqlalchemy import text


async def validate_database():
    """Validate database tables and data"""
    print("Validating Database...")
    print("-" * 30)
    
    try:
        sqlite_manager = get_sqlite_manager()
        
        async with sqlite_manager.get_connection() as conn:
            # Check tables exist
            result = await conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('query_forms', 'query_form_history')
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if 'query_forms' not in tables:
                print("ERROR: query_forms table missing")
                return False
                
            if 'query_form_history' not in tables:
                print("ERROR: query_form_history table missing")
                return False
            
            print("OK: Required tables exist")
            
            # Check data
            result = await conn.execute(text("SELECT COUNT(*) FROM query_forms"))
            form_count = result.fetchone()[0]
            print(f"OK: Found {form_count} query forms")
            
            # Check table structure
            result = await conn.execute(text("PRAGMA table_info(query_forms)"))
            columns = [row[1] for row in result.fetchall()]
            required_columns = ['id', 'form_name', 'sql_template', 'form_config', 'is_active']
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                print(f"ERROR: Missing columns: {missing_columns}")
                return False
            
            print("OK: All required columns present")
            
        return True
        
    except Exception as e:
        print(f"ERROR: Database validation failed: {e}")
        return False


async def validate_api_structure():
    """Validate API components"""
    print("\nValidating API Structure...")
    print("-" * 30)
    
    try:
        # Test core imports
        from app.models.schemas import QueryFormResponse, QueryFormCreate
        print("OK: Core schemas imported")
        
        from app.api.v1.endpoints.query_forms import router
        print("OK: API router imported")
        
        # Check route count
        route_count = len(router.routes)
        if route_count < 5:
            print(f"WARNING: Only {route_count} routes found, expected more")
        else:
            print(f"OK: Found {route_count} API routes")
        
        return True
        
    except Exception as e:
        print(f"ERROR: API validation failed: {e}")
        return False


async def validate_frontend_files():
    """Validate frontend files exist"""
    print("\nValidating Frontend Files...")
    print("-" * 30)
    
    try:
        frontend_files = [
            "frontend/src/types/query-forms.ts",
            "frontend/src/components/QueryFormBuilder.tsx",
            "frontend/src/components/DynamicForm.tsx",
            "frontend/src/pages/QueryForms/QueryFormManagement.tsx",
            "frontend/src/services/query-forms/query-form-api.ts"
        ]
        
        for file_path in frontend_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"OK: {file_path}")
            else:
                print(f"WARNING: {file_path} not found")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Frontend validation failed: {e}")
        return False


async def main():
    """Main validation function"""
    print("Query Forms System Validation")
    print("=" * 40)
    
    validators = [
        ("Database", validate_database),
        ("API Structure", validate_api_structure),
        ("Frontend Files", validate_frontend_files),
    ]
    
    results = []
    for name, validator in validators:
        try:
            result = await validator()
            results.append((name, result))
        except Exception as e:
            print(f"CRASH: {name} validation crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("VALIDATION SUMMARY")
    print("=" * 40)
    
    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:<15} {status}")
        if result:
            passed += 1
    
    print("-" * 40)
    print(f"TOTAL: {passed}/{len(results)} validations passed")
    
    if passed == len(results):
        print("\nSUCCESS: Query Forms system is ready!")
        print("\nNext steps:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. Open: http://localhost:8000/query-forms")
        print("3. Test the dynamic query form functionality")
        return True
    else:
        print(f"\nWARNING: {len(results) - passed} validation(s) failed")
        print("Please check the implementation before deployment")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
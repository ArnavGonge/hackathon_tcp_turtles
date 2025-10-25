# database.py
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import pandas as pd
from typing import List, Dict, Optional

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def query_to_dataframe(table: str, columns: str = '*', filters: Dict = None) -> pd.DataFrame:
    """
    Query Supabase table and return as DataFrame
    
    Args:
        table: Table name
        columns: Columns to select
        filters: Dict of {column: value} filters
    """
    query = supabase.table(table).select(columns)
    
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    
    response = query.execute()
    return pd.DataFrame(response.data)

def get_all_records(table: str, columns: str = '*') -> List[Dict]:
    """Get all records from a table"""
    response = supabase.table(table).select(columns).execute()
    return response.data

def get_single_record(table: str, filters: Dict, columns: str = '*') -> Optional[Dict]:
    """Get single record"""
    query = supabase.table(table).select(columns)
    for key, value in filters.items():
        query = query.eq(key, value)
    try:
        response = query.single().execute()
        return response.data
    except Exception as e:
        print(f"Error in get_single_record for table '{table}' with filters {filters}: {e}")
        import traceback
        traceback.print_exc()
        return None

def count_records(table: str, filters: Dict = None) -> int:
    """Count records in table"""
    query = supabase.table(table).select('*', count='exact')
    
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    
    response = query.execute()
    return response.count
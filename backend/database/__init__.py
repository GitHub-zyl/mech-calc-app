"""database package init"""
from .history_db import (
    init_db, add_record, get_record, list_records,
    delete_record, delete_records, count_records,
    stats_by_category, clear_all, get_db_path,
)

__all__ = [
    'init_db', 'add_record', 'get_record', 'list_records',
    'delete_record', 'delete_records', 'count_records',
    'stats_by_category', 'clear_all', 'get_db_path',
]

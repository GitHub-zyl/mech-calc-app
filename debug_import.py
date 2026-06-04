"""Debug script"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

try:
    from backend.api.data import bp
    print(f'OK bp={bp} name={bp.name}')
except Exception as e:
    import traceback
    traceback.print_exc()

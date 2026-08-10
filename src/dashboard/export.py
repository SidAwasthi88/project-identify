import pandas as pd
import os
import sys

# Ensure parent directory is in sys.path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_queries import get_attendance_by_subject, get_attendance_for_session

def _format_name(row):
    """Helper to format full name without commas if split across columns."""
    if 'full_name' in row and row['full_name']:
        return row['full_name']
    
    first = str(row.get('first_name', '') or '').strip()
    middle = str(row.get('middle_name', '') or '').strip()
    last = str(row.get('last_name', '') or '').strip()
    
    if middle:
        return f"{first} {middle} {last}".strip()
    return f"{first} {last}".strip()

def export_subject_attendance_csv(subject_id: int, output_path: str = None) -> str:
    """Exports attendance records for a specific subject to CSV."""
    records = get_attendance_by_subject(subject_id)
    if not records:
        return None
        
    df = pd.DataFrame(records)
    
    # Handle name formatting cleanly
    if 'first_name' in df.columns and 'last_name' in df.columns:
        df['Name'] = df.apply(_format_name, axis=1)
    elif 'full_name' in df.columns:
        df['Name'] = df['full_name']

    # Column mapping
    column_mapping = {
        'reg_no': 'Reg No.',
        'roll_no': 'Roll No.',
        'date': 'Date',
        'start_time': 'Session Start',
        'status': 'Status',
        'marked_by': 'Marked By'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Select and order final relevant columns if available
    desired_cols = ['Reg No.', 'Roll No.', 'Name', 'Date', 'Session Start', 'Status', 'Marked By']
    export_cols = [col for col in desired_cols if col in df.columns]
    
    if export_cols:
        df = df[export_cols]

    if output_path is None:
        output_path = f"attendance_subject_{subject_id}.csv"
        
    df.to_csv(output_path, index=False)
    return output_path

def export_session_attendance_csv(session_id: int, output_path: str = None) -> str:
    """Exports attendance records for a single session to CSV."""
    records = get_attendance_for_session(session_id)
    if not records:
        return None
        
    df = pd.DataFrame(records)
    
    # Handle name formatting cleanly
    if 'first_name' in df.columns and 'last_name' in df.columns:
        df['Name'] = df.apply(_format_name, axis=1)
    elif 'full_name' in df.columns:
        df['Name'] = df['full_name']

    # Column mapping
    column_mapping = {
        'reg_no': 'Reg No.',
        'roll_no': 'Roll No.',
        'status': 'Status',
        'marked_by': 'Marked By',
        'marked_at': 'Marked At'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Select and order final relevant columns if available
    desired_cols = ['Reg No.', 'Roll No.', 'Name', 'Status', 'Marked By', 'Marked At']
    export_cols = [col for col in desired_cols if col in df.columns]
    
    if export_cols:
        df = df[export_cols]

    if output_path is None:
        output_path = f"attendance_session_{session_id}.csv"
        
    df.to_csv(output_path, index=False)
    return output_path
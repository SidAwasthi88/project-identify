import pandas as pd
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_queries import get_attendance_by_subject, get_attendance_for_session

def export_subject_attendance_csv(subject_id: int, output_path: str = None) -> str:
    records = get_attendance_by_subject(subject_id)
    if not records:
        return None
        
    df = pd.DataFrame(records)
    df = df.rename(columns={
        'reg_no': 'Reg No.',
        'roll_no': 'Roll No.',
        'full_name': 'Name',
        'date': 'Date',
        'start_time': 'Session Start',
        'status': 'Status',
        'marked_by': 'Marked By'
    })
    
    if output_path is None:
        output_path = f"attendance_subject_{subject_id}.csv"
        
    df.to_csv(output_path, index=False)
    return output_path

def export_session_attendance_csv(session_id: int, output_path: str = None) -> str:
    records = get_attendance_for_session(session_id)
    if not records:
        return None
        
    df = pd.DataFrame(records)
    df = df.rename(columns={
        'reg_no': 'Reg No.',
        'roll_no': 'Roll No.',
        'full_name': 'Name',
        'status': 'Status',
        'marked_by': 'Marked By',
        'marked_at': 'Marked At'
    })
    
    if output_path is None:
        output_path = f"attendance_session_{session_id}.csv"
        
    df.to_csv(output_path, index=False)
    return output_path
"""Import Section D students and weekly timetable into the database."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.store import Store

ROOT = Path(__file__).resolve().parents[1]

TIMETABLE = [
    # Monday
    {'weekday': 0, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Computer Networks Lab', 'course_code': 'CN Lab', 'teacher': 'ART', 'room': 'L2', 'batch': 'D1', 'is_lab': True},
    {'weekday': 0, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Digital Image Processing Lab', 'course_code': 'DIP Lab', 'teacher': 'BMH', 'room': 'L1', 'batch': 'D2', 'is_lab': True},
    {'weekday': 0, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Deep Learning Lab', 'course_code': 'DL Lab', 'teacher': 'AA', 'room': 'L4', 'batch': 'D3', 'is_lab': True},
    {'weekday': 0, 'start_time': '11:00', 'end_time': '12:00', 'course_name': 'Deep Learning', 'course_code': 'DL', 'teacher': 'Samina Anjum', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 0, 'start_time': '13:00', 'end_time': '14:00', 'course_name': 'Computer Networks', 'course_code': 'CN', 'teacher': 'LMH', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 0, 'start_time': '14:00', 'end_time': '15:00', 'course_name': 'Digital Image Processing', 'course_code': 'DIP', 'teacher': 'BMH', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 0, 'start_time': '15:00', 'end_time': '16:00', 'course_name': 'Cloud Fundamentals', 'course_code': 'PE-1 Cloud', 'teacher': 'NSD', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    # Tuesday
    {'weekday': 1, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Computer Networks Lab', 'course_code': 'CN Lab', 'teacher': 'ART', 'room': 'L2', 'batch': 'D3', 'is_lab': True},
    {'weekday': 1, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Business Communication Lab', 'course_code': 'BC Lab', 'teacher': 'Rohan', 'room': 'B 0/6', 'batch': 'D2', 'is_lab': True},
    {'weekday': 1, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Deep Learning Lab', 'course_code': 'DL Lab', 'teacher': 'AA', 'room': 'L4', 'batch': 'D1', 'is_lab': True},
    {'weekday': 1, 'start_time': '11:00', 'end_time': '12:00', 'course_name': 'Cloud Fundamentals', 'course_code': 'PE-1 Cloud', 'teacher': 'NSD', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 1, 'start_time': '13:00', 'end_time': '14:00', 'course_name': 'Deep Learning', 'course_code': 'DL', 'teacher': 'Samina Anjum', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 1, 'start_time': '14:00', 'end_time': '15:00', 'course_name': 'Computer Networks', 'course_code': 'CN', 'teacher': 'LMH', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 1, 'start_time': '15:00', 'end_time': '17:00', 'course_name': 'Cloud Fundamentals Lab', 'course_code': 'Cloud Lab', 'teacher': 'KK', 'room': 'L1', 'batch': 'D1', 'is_lab': True},
    # Wednesday
    {'weekday': 2, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Digital Image Processing Lab', 'course_code': 'DIP Lab', 'teacher': 'BMH', 'room': 'L1', 'batch': 'D1', 'is_lab': True},
    {'weekday': 2, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Deep Learning Lab', 'course_code': 'DL Lab', 'teacher': 'AA', 'room': 'L4', 'batch': 'D2', 'is_lab': True},
    {'weekday': 2, 'start_time': '09:00', 'end_time': '11:00', 'course_name': 'Business Communication Lab', 'course_code': 'BC Lab', 'teacher': 'Ajinkya', 'room': 'B 0/6', 'batch': 'D3', 'is_lab': True},
    {'weekday': 2, 'start_time': '11:00', 'end_time': '12:00', 'course_name': 'Deep Learning', 'course_code': 'DL', 'teacher': 'Samina Anjum', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 2, 'start_time': '13:00', 'end_time': '15:00', 'course_name': 'Cloud Fundamentals Lab', 'course_code': 'Cloud Lab', 'teacher': 'NSD', 'room': 'M. Tech Lab', 'batch': 'D2', 'is_lab': True},
    # Thursday
    {'weekday': 3, 'start_time': '10:00', 'end_time': '11:00', 'course_name': 'Digital Image Processing', 'course_code': 'DIP', 'teacher': 'BMH', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 3, 'start_time': '11:00', 'end_time': '12:00', 'course_name': 'Cloud Fundamentals', 'course_code': 'PE-1 Cloud', 'teacher': 'NSD', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 3, 'start_time': '13:00', 'end_time': '15:00', 'course_name': 'Business Communication Lab', 'course_code': 'BC Lab', 'teacher': 'Ajinkya', 'room': 'B 0/6', 'batch': 'D1', 'is_lab': True},
    {'weekday': 3, 'start_time': '13:00', 'end_time': '15:00', 'course_name': 'Computer Networks Lab', 'course_code': 'CN Lab', 'teacher': 'LMH', 'room': 'L2', 'batch': 'D2', 'is_lab': True},
    {'weekday': 3, 'start_time': '13:00', 'end_time': '15:00', 'course_name': 'Digital Image Processing Lab', 'course_code': 'DIP Lab', 'teacher': 'BMH', 'room': 'L1', 'batch': 'D3', 'is_lab': True},
    # Friday
    {'weekday': 4, 'start_time': '10:00', 'end_time': '11:00', 'course_name': 'Computer Networks', 'course_code': 'CN', 'teacher': 'LMH', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 4, 'start_time': '11:00', 'end_time': '12:00', 'course_name': 'Digital Image Processing', 'course_code': 'DIP', 'teacher': 'BMH', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 4, 'start_time': '13:00', 'end_time': '14:00', 'course_name': 'Open Elective III / MOOCs', 'course_code': 'OE', 'teacher': 'Nikhil', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    # Saturday
    {'weekday': 5, 'start_time': '10:00', 'end_time': '11:00', 'course_name': 'Business Communication', 'course_code': 'BC', 'teacher': 'RN', 'room': 'B 00/6', 'batch': None, 'is_lab': False},
    {'weekday': 5, 'start_time': '12:00', 'end_time': '14:00', 'course_name': 'Cloud Fundamentals Lab', 'course_code': 'Cloud Lab', 'teacher': 'KK', 'room': 'L1', 'batch': 'D3', 'is_lab': True},
]


def main():
    import os
    db_path = os.environ.get('ATTEND_DB', str(ROOT / 'data' / 'attendance.db'))

    # Back up old database if it exists
    old = Path(db_path)
    if old.exists():
        backup = old.with_suffix('.db.bak')
        if not backup.exists():
            import shutil
            shutil.copy2(old, backup)
            print(f'Backed up existing database to {backup}')
        old.unlink()
        # Also remove WAL/SHM files
        for suffix in ('.db-wal', '.db-shm'):
            p = Path(str(old) + suffix.replace('.db', ''))
            if p.exists():
                p.unlink()
        print('Removed old database for fresh schema')

    store = Store(db_path)

    # Import students
    roster_path = ROOT / 'data' / 'imports' / 'section-d-students.json'
    if not roster_path.exists():
        print(f'Student roster not found at {roster_path}')
        return

    students = json.loads(roster_path.read_text(encoding='utf-8'))
    count = 0
    for s in students:
        try:
            store.add_student(
                roll_no=s['roll_no'],
                name=s['name'],
                email=s.get('email'),
                section=s.get('section', 'D'),
                batch=s.get('batch'),
                photo_path=s.get('photo_path')
            )
            count += 1
        except Exception as e:
            print(f'  Skipped {s["roll_no"]}: {e}')
    print(f'Imported {count} students')

    # Import timetable
    tt_count = 0
    for rule in TIMETABLE:
        store.add_timetable_rule(**rule)
        tt_count += 1
    print(f'Imported {tt_count} timetable rules')

    print('Seed complete.')


if __name__ == '__main__':
    main()

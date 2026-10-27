"""Auto-seed the database with Section D students and timetable on first run.

On Render (and any ephemeral filesystem), the SQLite database is wiped on every
deploy/restart.  This module embeds the seed data directly in Python so it
ships with the Docker image and is always available — no external JSON files
needed.
"""
import logging
from .store import Store

log = logging.getLogger(__name__)

# ── Section D student roster ────────────────────────────────────────────────

STUDENTS = [
    {"roll_no": "D-1", "name": "Aaditee Ashwin Bhope", "email": "24bhopea@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-2", "name": "Aastha Dinkar Pardikar", "email": "24pardikara@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-3", "name": "Abhijeet Gurnule", "email": "24gurnulea@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-4", "name": "Aditi patel", "email": "24patela_1@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-5", "name": "Armaan Jijotia", "email": "24jijotiaa@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-6", "name": "ARYA MOHOD", "email": "24mohoda@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-7", "name": "Arya Paunikar", "email": "24paunikara@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-8", "name": "Atharva Korde", "email": "24kordea@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-9", "name": "Ayaan Ahmed", "email": "24ahmeda@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-10", "name": "Bharat Vilas Digrase", "email": "24digraseb@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-11", "name": "Darsh kadu", "email": "24kadud@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-12", "name": "Dev Joshi", "email": "24joshid_2@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-13", "name": "Dhruv Narendra khedkar", "email": "24khedkard@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-14", "name": "Divyam Sharma", "email": "24sharmad_2@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-15", "name": "Divyatwa Kirnapure", "email": "24kirnapured@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-16", "name": "Hargun Singh Jaggi", "email": "24jaggih@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-17", "name": "Harshal Tarwale", "email": "24tarwaleh@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-18", "name": "Janhavi Gulhane", "email": "24gulhanej@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-19", "name": "Kanak Lulla", "email": "24lullak@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-20", "name": "Kshitij Panday", "email": "24pandayk@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-21", "name": "Kunal S. Gadwani", "email": "24gadwanik@rbunagpur.in", "section": "D", "batch": "D1"},
    {"roll_no": "D-22", "name": "Lalit Morwani", "email": "24morwanil@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-23", "name": "Latisha Mayaramani", "email": "24mayaramanil@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-24", "name": "Mayank S. Gupta", "email": "24guptam@rbungapur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-25", "name": "Md. Rowhan Haque", "email": "24haquem@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-26", "name": "Minal Gahlot", "email": "24gahlotm@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-27", "name": "Mithilesh Bhave", "email": "24bhavem@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-28", "name": "Mrunmayee Tadaskar", "email": "24tadaskarm@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-29", "name": "Nirbhay Shinganjude", "email": "24shinganjuden@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-30", "name": "Onkar Dattatrya Paitwar", "email": "24paitwaro@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-31", "name": "Palak Chimurkar", "email": "24chimurkarp@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-32", "name": "Palak Khubnani", "email": "24khubnanip@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-33", "name": "Pawni Ashish Thanekar", "email": "24thanekarp@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-34", "name": "Pranav Bangare", "email": "24bangarep@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-35", "name": "PRASHIL PATIL", "email": "24patilp@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-36", "name": "Prathamesh dhote", "email": "24dhotep@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-37", "name": "Prathmesh Rane", "email": "24ranep@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-38", "name": "Priya Jitendra keshwani", "email": "24keshwanip@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-39", "name": "Pushkar Wankhede", "email": "24wankhedep@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-40", "name": "Ritesh Arun Bande", "email": "24bander@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-41", "name": "Rudresh Patil", "email": "24patilr@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-42", "name": "Sanika Nilesh Shadarpawar", "email": "24shadarpawars@rbunagpur.in", "section": "D", "batch": "D2"},
    {"roll_no": "D-43", "name": "Shashwat Sinha", "email": "24sinhas@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-44", "name": "Shweta Dayama", "email": "24dayamas@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-45", "name": "Siddharth Dwivedi", "email": "24dwivedis@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-46", "name": "Soumya Agrawal", "email": "24agrawals_7@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-47", "name": "Srujal Bisen", "email": "24bisens@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-48", "name": "Suhani Mishra", "email": "24mishras_1@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-49", "name": "Sujal Puniyani", "email": "24puniyanis@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-50", "name": "Swaraj Lakhe", "email": "24lakhes@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-51", "name": "Swaraj yeole", "email": "24yeoles@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-52", "name": "Syed Albash Ali", "email": "24alis@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-53", "name": "Tanmay Paliwal", "email": "24paliwalt@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-54", "name": "Tanvi pandey", "email": "24pandeyt@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-55", "name": "Tilak Sorte", "email": "24sortet@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-56", "name": "Uzayr Sheikh", "email": "24sheikhu@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-57", "name": "Vaibhavi Badwaik", "email": "24badwaikv@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-58", "name": "Vedant Bele", "email": "24belev@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-59", "name": "VEDIKA AMRITKAR", "email": "24amritkar.v@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-60", "name": "Vismay shende", "email": "24shendev@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-61", "name": "Vyakhya Goyal", "email": "24goyalv@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-62", "name": "Yash Daryani", "email": "24daryaniy@rbunagpur.in", "section": "D", "batch": "D3"},
    {"roll_no": "D-63", "name": "Zaid shaikh", "email": "24shaikhz@gmail.com", "section": "D", "batch": "D3"},
]

# ── Weekly timetable ────────────────────────────────────────────────────────

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


def auto_seed(store: Store) -> None:
    """Seed students and timetable if the database is empty.

    Safe to call on every startup — it only inserts when both tables are empty,
    so it won't duplicate data if the database already has content.
    """
    with store.connect() as db:
        student_count = db.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        timetable_count = db.execute(
            'SELECT COUNT(*) FROM timetable_rules').fetchone()[0]

    if student_count > 0 or timetable_count > 0:
        log.info('Database already has data (%d students, %d rules) — '
                 'skipping auto-seed.', student_count, timetable_count)
        return

    log.info('Empty database detected — seeding %d students and %d '
             'timetable rules …', len(STUDENTS), len(TIMETABLE))

    imported = 0
    for s in STUDENTS:
        try:
            store.add_student(
                roll_no=s['roll_no'],
                name=s['name'],
                email=s.get('email'),
                section=s.get('section', 'D'),
                batch=s.get('batch'),
            )
            imported += 1
        except Exception as exc:
            log.warning('Skipped %s: %s', s['roll_no'], exc)

    tt_count = 0
    for rule in TIMETABLE:
        store.add_timetable_rule(**rule)
        tt_count += 1

    log.info('Auto-seed complete: %d students, %d timetable rules.',
             imported, tt_count)

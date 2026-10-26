import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS students(
                id TEXT PRIMARY KEY,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                section TEXT NOT NULL DEFAULT 'D',
                batch TEXT,
                photo_path TEXT,
                consent_at TEXT,
                samples TEXT,
                centroid TEXT
            );

            CREATE TABLE IF NOT EXISTS timetable_rules(
                id TEXT PRIMARY KEY,
                weekday INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                course_name TEXT NOT NULL,
                course_code TEXT,
                teacher TEXT,
                room TEXT,
                batch TEXT,
                is_lab INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS timetable_exceptions(
                id TEXT PRIMARY KEY,
                rule_id TEXT REFERENCES timetable_rules(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                action TEXT NOT NULL DEFAULT 'cancel',
                replacement TEXT,
                reason TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions(
                id TEXT PRIMARY KEY,
                rule_id TEXT REFERENCES timetable_rules(id),
                name TEXT NOT NULL,
                date TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_active ON sessions((1)) WHERE ended_at IS NULL;

            CREATE TABLE IF NOT EXISTS attendance(
                student_id TEXT REFERENCES students(id) ON DELETE CASCADE,
                session_id TEXT REFERENCES sessions(id),
                status TEXT NOT NULL DEFAULT 'present',
                similarity REAL,
                marked_at TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'face',
                PRIMARY KEY(student_id, session_id)
            );

            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);

            CREATE TABLE IF NOT EXISTS probes(
                id TEXT PRIMARY KEY,
                split TEXT,
                subject TEXT,
                batch TEXT,
                expected TEXT,
                scores TEXT,
                latency REAL,
                created_at TEXT
            );
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db

    # ── Students ──────────────────────────────────────────────

    def students(self, vectors=False):
        with self.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM students ORDER BY roll_no')]
        for r in rows:
            if r.get('samples'):
                r['sample_count'] = len(json.loads(r['samples']))
            else:
                r['sample_count'] = 0
            if vectors and r.get('centroid'):
                r['centroid'] = json.loads(r['centroid'])
            else:
                r.pop('centroid', None)
            r.pop('samples', None)

        def _roll_key(s):
            m = re.search(r'\d+', s.get('roll_no') or '')
            return int(m.group(0)) if m else 9999

        rows.sort(key=_roll_key)
        return rows

    def get_student(self, sid):
        with self.connect() as db:
            row = db.execute('SELECT * FROM students WHERE id=?', (sid,)).fetchone()
        if not row:
            raise ValueError('Student not found')
        r = dict(row)
        if r.get('samples'):
            r['sample_count'] = len(json.loads(r['samples']))
        else:
            r['sample_count'] = 0
        r.pop('samples', None)
        r.pop('centroid', None)
        return r

    def add_student(self, roll_no, name, email=None, section='D', batch=None,
                    photo_path=None, samples=None, centroid=None, consent_at=None):
        pid = str(uuid.uuid4())
        with self.connect() as db:
            db.execute(
                'INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?,?)',
                (pid, roll_no, name, email, section, batch, photo_path,
                 consent_at or (now() if samples else None),
                 json.dumps(samples) if samples else None,
                 json.dumps(centroid) if centroid else None)
            )
        return pid

    def update_student_enrollment(self, sid, samples, centroid, photo_path=None):
        """Update face embeddings for an existing student."""
        with self.connect() as db:
            updates = {'samples': json.dumps(samples), 'centroid': json.dumps(centroid),
                       'consent_at': now()}
            if photo_path:
                updates['photo_path'] = photo_path
            sets = ', '.join(f'{k}=?' for k in updates)
            db.execute(f'UPDATE students SET {sets} WHERE id=?',
                       (*updates.values(), sid))
            self.invalidate(db)

    def invalidate(self, db):
        db.execute('DELETE FROM probes')
        db.execute("DELETE FROM settings WHERE key='calibration'")

    def delete_student(self, sid):
        with self.connect() as db:
            if not db.execute('DELETE FROM students WHERE id=?', (sid,)).rowcount:
                raise ValueError('Student not found')
            self.invalidate(db)

    # ── Timetable ─────────────────────────────────────────────

    def timetable_rules(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                'SELECT * FROM timetable_rules ORDER BY weekday, start_time')]

    def add_timetable_rule(self, weekday, start_time, end_time, course_name,
                           teacher=None, room=None, batch=None, is_lab=False,
                           course_code=None):
        rid = str(uuid.uuid4())
        with self.connect() as db:
            db.execute(
                'INSERT INTO timetable_rules VALUES(?,?,?,?,?,?,?,?,?,?)',
                (rid, weekday, start_time, end_time, course_name, course_code,
                 teacher, room, batch, int(is_lab))
            )
        return rid

    def update_timetable_rule(self, rid, **kwargs):
        allowed = {'weekday', 'start_time', 'end_time', 'course_name', 'course_code',
                   'teacher', 'room', 'batch', 'is_lab'}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        if 'is_lab' in updates:
            updates['is_lab'] = int(updates['is_lab'])
        with self.connect() as db:
            sets = ', '.join(f'{k}=?' for k in updates)
            if not db.execute(f'UPDATE timetable_rules SET {sets} WHERE id=?',
                              (*updates.values(), rid)).rowcount:
                raise ValueError('Timetable rule not found')

    def delete_timetable_rule(self, rid):
        with self.connect() as db:
            if not db.execute('DELETE FROM timetable_rules WHERE id=?', (rid,)).rowcount:
                raise ValueError('Timetable rule not found')

    def timetable_exceptions(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                'SELECT * FROM timetable_exceptions ORDER BY date')]

    def add_timetable_exception(self, rule_id, date, action='cancel',
                                replacement=None, reason=None):
        eid = str(uuid.uuid4())
        with self.connect() as db:
            db.execute(
                'INSERT INTO timetable_exceptions VALUES(?,?,?,?,?,?,?)',
                (eid, rule_id, date, action,
                 json.dumps(replacement) if replacement else None,
                 reason, now())
            )
        return eid

    def delete_timetable_exception(self, eid):
        with self.connect() as db:
            if not db.execute('DELETE FROM timetable_exceptions WHERE id=?',
                              (eid,)).rowcount:
                raise ValueError('Exception not found')

    def today_schedule(self, weekday, date_str):
        """Get schedule for a given weekday, applying exceptions for the date."""
        rules = [r for r in self.timetable_rules() if r['weekday'] == weekday]
        exceptions = {e['rule_id']: e for e in self.timetable_exceptions()
                      if e['date'] == date_str}
        schedule = []
        for rule in rules:
            exc = exceptions.get(rule['id'])
            if exc and exc['action'] == 'cancel':
                continue
            if exc and exc['action'] == 'replace' and exc.get('replacement'):
                replacement = json.loads(exc['replacement']) if isinstance(
                    exc['replacement'], str) else exc['replacement']
                merged = {**rule, **replacement, 'exception_id': exc['id']}
                schedule.append(merged)
            else:
                schedule.append(rule)
        return schedule

    # ── Sessions ──────────────────────────────────────────────

    def sessions(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                'SELECT * FROM sessions ORDER BY started_at DESC')]

    def start_session(self, name, rule_id=None, date=None):
        sid = str(uuid.uuid4())
        try:
            with self.connect() as db:
                db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,NULL)',
                           (sid, rule_id, name, date, now()))
        except sqlite3.IntegrityError:
            raise ValueError('End the active session before starting another')
        return sid

    def end_session(self, sid):
        with self.connect() as db:
            if not db.execute(
                    'UPDATE sessions SET ended_at=? WHERE id=? AND ended_at IS NULL',
                    (now(), sid)).rowcount:
                raise ValueError('Active session not found')

    def active_session(self):
        with self.connect() as db:
            row = db.execute(
                'SELECT * FROM sessions WHERE ended_at IS NULL').fetchone()
        return dict(row) if row else None

    # ── Attendance ────────────────────────────────────────────

    def mark(self, student_id, session_id, score, method='face'):
        with self.connect() as db:
            if not db.execute(
                    'SELECT 1 FROM sessions WHERE id=? AND ended_at IS NULL',
                    (session_id,)).fetchone():
                raise ValueError('Start an attendance session first')
            return bool(db.execute(
                'INSERT OR IGNORE INTO attendance VALUES(?,?,?,?,?,?)',
                (student_id, session_id, 'present', score, now(), method)
            ).rowcount)

    def mark_absent_remaining(self, session_id, eligible_student_ids):
        """Mark all students who were not already marked present as absent."""
        with self.connect() as db:
            for sid in eligible_student_ids:
                db.execute(
                    'INSERT OR IGNORE INTO attendance VALUES(?,?,?,?,?,?)',
                    (sid, session_id, 'absent', None, now(), 'auto')
                )

    def records(self, session_id=None, date=None):
        with self.connect() as db:
            query = '''SELECT s.name AS student_name, s.roll_no, s.section, s.batch,
                       a.status, a.similarity, a.marked_at, a.method,
                       a.student_id, a.session_id,
                       sess.name AS session_name, sess.date AS session_date,
                       sess.started_at
                       FROM attendance a
                       JOIN students s ON s.id=a.student_id
                       JOIN sessions sess ON sess.id=a.session_id'''
            params = []
            conditions = []
            if session_id:
                conditions.append('a.session_id=?')
                params.append(session_id)
            if date:
                conditions.append('sess.date=?')
                params.append(date)
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            rows = [dict(r) for r in db.execute(query, params)]
            def _roll_key(s):
                m = re.search(r'\d+', s.get('roll_no') or '')
                return int(m.group(0)) if m else 9999
            rows.sort(key=_roll_key)
            return rows

    def all_records(self):
        """Legacy-compatible: return all attendance records."""
        with self.connect() as db:
            return [dict(r) for r in db.execute('''
                SELECT s.name, s.roll_no AS student_id, a.*, sess.name AS session_name
                FROM attendance a JOIN students s ON s.id=a.student_id
                JOIN sessions sess ON sess.id=a.session_id
                ORDER BY a.marked_at DESC''')]

    # ── Settings ──────────────────────────────────────────────

    def setting(self, key, default=None):
        with self.connect() as db:
            r = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return json.loads(r[0]) if r else default

    def set_setting(self, key, value):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',
                       (key, json.dumps(value)))

    # ── Probes (Accuracy Lab) ─────────────────────────────────

    def probes(self):
        with self.connect() as db:
            rows = [dict(r) for r in db.execute(
                'SELECT * FROM probes ORDER BY created_at')]
        for r in rows:
            r['scores'] = json.loads(r['scores'])
        return rows

    def add_probe(self, split, subject, batch, expected, scores, latency):
        with self.connect() as db:
            existing = db.execute(
                'SELECT split, expected, subject, batch FROM probes').fetchall()
            for r in existing:
                if (r['split'] != split and
                        (r['batch'] == batch or
                         (expected is None and r['expected'] is None
                          and r['subject'] == subject))):
                    raise ValueError(
                        'Use separate capture batches and separate unknown '
                        'students for validation and test')
            db.execute(
                'INSERT INTO probes VALUES(?,?,?,?,?,?,?,?)',
                (str(uuid.uuid4()), split, subject, batch, expected,
                 json.dumps(scores), latency, now()))

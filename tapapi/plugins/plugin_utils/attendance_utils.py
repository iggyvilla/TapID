from datetime import datetime

def insert_into_attendance_logs(name: str, uid: str, conn):
    with conn:
        with conn.cursor() as curs:
            curs.execute('insert into attendance (name, uid, date) values (%s, %s, %s)', (name, uid, datetime.now()))

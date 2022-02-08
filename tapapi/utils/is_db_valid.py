import psycopg2.errors


def is_db_valid(conn):

    with conn:
        with conn.cursor() as curs:
            try:
                curs.execute('select * from metrics;')
                curs.execute('select * from public_keys;')
                curs.execute('select * from test_key_pairs;')
            except psycopg2.errors.Error:
                return False

            return True
import psycopg2


def get_balance_of_uid(conn, uid: str) -> int:
    with conn:
        with conn.cursor() as curs:
            curs.execute("select balance from canteen_chits where uid = %s;", (uid,))
            row = curs.fetchone()

            if not row:
                curs.execute("insert into canteen_chits (uid, balance) values (%s, 0)", (uid,))
                curs.execute("select balance from canteen_chits where uid = %s;", (uid,))
                return curs.fetchone()

            return row[0]


def update_balance_of_uid(conn, uid, new_bal) -> int:
    with conn:
        with conn.cursor() as curs:
            curs.execute("update canteen_chits set balance = %s where uid = %s;", (new_bal, uid))

            return True


if __name__ == "__main__":
    # Just some test code
    conn = psycopg2.connect(user="enriquevilla",
                            password="fuzzii",
                            host="localhost",
                            port="5432",
                            database="tapid")

    print(get_balance_of_uid(conn, '00 00 00 00'))

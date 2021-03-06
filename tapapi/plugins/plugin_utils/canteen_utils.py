import psycopg2
from datetime import datetime


def get_balance_of_uid(conn, uid: str) -> int:
    with conn:
        with conn.cursor() as curs:
            curs.execute("select balance from canteen_chits where uid = %s;", (uid,))
            row = curs.fetchone()

            # If the card still hasn't been registered with a balance, add it to the database
            if not row:
                curs.execute("insert into canteen_chits (uid, balance) values (%s, 0)", (uid,))
                curs.execute("select balance from canteen_chits where uid = %s;", (uid,))
                return curs.fetchone()

            return row[0]


def update_balance_of_uid(conn, uid, new_bal: int, action, bal) -> int:
    if action == "subtract":
        action = 0
    elif action == "add":
        action = 1

    with conn:
        with conn.cursor() as curs:
            # Update the balance with the new_bal
            curs.execute("update canteen_chits set balance = %s where uid = %s;", (new_bal, uid))
            # Add to logs
            curs.execute("insert into canteen_transactions (timestamp, uid, action, new_bal, amount) values (%s, %s, %s, %s, %s)", (datetime.now(), uid, action, bal, new_bal))
            return True


if __name__ == "__main__":
    # Just some test code
    conn = psycopg2.connect(user="enriquevilla",
                            password="fuzzii",
                            host="localhost",
                            port="5432",
                            database="tapid")

    print(get_balance_of_uid(conn, '00 00 00 00'))

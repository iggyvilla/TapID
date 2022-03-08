from datetime import datetime, timedelta


def get_books_from_uid(uid: str, conn):
    """
    Get a UID's associated borrowed books
    """
    with conn:
        with conn.cursor() as curs:
            # This one's a good example of when it is most critical to use template strings for the SQL query
            #  because users input data, one could do an SQL injection attack if you did not use the %s
            curs.execute("select borrow_id, b.book_name, due_on from books_borrowed p inner join book_ids b on b.book_id = p.book_id AND p.uid = %s;", (uid,))
            return curs.fetchall()


def borrow_book(uid: str, book_id: int, due_on: int, conn):
    """
    Insert a borrowed book into the database
    """
    with conn:
        with conn.cursor() as curs:
            curs.execute(
                "insert into books_borrowed (book_id, due_on, uid) values (%s, %s, %s)",
                (book_id, datetime.now() + timedelta(days=due_on), uid)
            )

            curs.execute("select borrow_id, b.book_name, due_on from books_borrowed p inner join book_ids b on b.book_id = p.book_id AND p.uid = %s;", (uid,))

            # Select the just added row so we can update the google sheets file with a book number
            return curs.fetchone()

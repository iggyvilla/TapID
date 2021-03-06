import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


username = input("Enter your database username:\n")
password = input("Enter your database password:\n")

conn = psycopg2.connect(user=username,
                        password=password,
                        host="localhost",
                        port="5432",
                        database="postgres")

# To make a database without it erroring
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)


conn.cursor().execute('create database tapid;')

conn = psycopg2.connect(user=username,
                        password=password,
                        host="localhost",
                        port="5432",
                        database="tapid")

with conn:
    with conn.cursor() as curs:
        curs.execute("""
            create table public_keys (
                uid varchar(11) primary key,
                public_key text unique
            );
        """)

        curs.execute("""
            create table test_key_pairs (
                uid varchar(11) primary key,
                private_key text,
                public_key text
            );
        """)

        curs.execute("""
            create table metrics (
                metric_id serial primary key,
                event_name text,
                metric_data json,
                timestamp timestamp
            );
        """)

        curs.execute("""
            create table books_borrowed (
                borrow_id serial primary key,
                book_id int references book_ids(book_id) not null,
                due_on date not null
            );
        """)

        curs.execute("""
            create table book_ids (
                book_id serial primary key,
                book_name text
            );
        """)

        curs.execute("""
            create table canteen_chits (
                transaction_number serial primary key,
                uid varchar(11),
                balance integer
            );
        """)

print("Made database with no errors!")

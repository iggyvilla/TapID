import string
import logging
import jwt
import random
import psycopg2
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

_log = logging.getLogger("main.logger")


def _generate_fake_uid():
    """Makes a fake RFID UID"""
    # Don't you love Python one-line magic
    return ' '.join([''.join(random.choices(string.hexdigits.upper()[:-6], k=2)) for _ in range(4)])


def generate_key_pairs(to_database=False, conn=None, uid=None):
    """
    Generates an RSA key pair
    :param to_database: if to send to the database configured in connect_to_database()
    :param conn: The Psycopg2 connection object
    :returns: utf-8 decrypted (public_key, private_key)
    """

    # 65537 as a public exponent is standard (e=3 is used sometimes, but a
    #  student can do future research on the security of this RSA implementation)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # What's all this PEM, PKCS8, PKCS1 stuff?
    # Read: https://stackoverflow.com/questions/48958304/pkcs1-and-pkcs8-format-for-rsa-private-key
    encrypted_pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    encrypted_pem_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1
    )

    # The private keys come in a byte-encoded format, so we turn it into a string by using .decode('utf-8')
    utf8_pem_private_key = encrypted_pem_private_key.decode('utf-8')
    utf8_pem_public_key = encrypted_pem_public_key.decode('utf-8')

    if to_database:
        if not conn or not uid:
            return ValueError("No connection/uid object provided")

        # Connect to TapID database (see connect_to_database() for more details)
        connection = conn

        # We use cursors to send commands to databases through cursor.execute()
        cursor = connection.cursor()

        # ALWAYS use query parameters to prevent SQL injection
        item_tuple = (uid, utf8_pem_private_key, utf8_pem_public_key)
        cursor.execute('insert into test_key_pairs (uid, private_key, public_key) values (%s, %s, %s);', item_tuple)

        # Commit the connection
        # You can commit this way, or check get_public_key_from_uid to see another way to automatically connect
        #  using context managers
        connection.commit()

    return utf8_pem_public_key, utf8_pem_private_key


def get_public_key_from_uid(uid: str, conn, save_priv_key_on_new_uid=False):
    """
    Get a public key from a card UID.

    :param uid: The UID of the card (casted to string)
    :param conn: The Psycopg2 connection object
    :param save_priv_key_on_new_uid: Whether to save the private key to an external table named test_key_pairs.
     Could be used when generating card UIDs at first.
    :return: An error (check DB configuration), and a tuple consisting of (uid, public_key) when successful
    """

    try:

        # Create a cursor to perform database operations
        # Use context managers to make more readable (and error-safe code)
        with conn:
            with conn.cursor() as curs:
                # Get the public key associated with the UID
                curs.execute("select * from public_keys where uid = %s;", (uid,))

                # Returned result
                row = curs.fetchone()

                # Check if the row exists
                if row is None:
                    # Generate a new RSA key pair
                    public_key, private_key = generate_key_pairs()

                    # Insert into the public_keys database (row 1 - uid, row 2 - public_key)
                    curs.execute("insert into public_keys (uid, public_key) values (%s, %s);", (uid, public_key))

                    if save_priv_key_on_new_uid:
                        # Insert the key pair into the test_key_pairs database
                        curs.execute("insert into test_key_pairs (uid, public_key, private_key) values (%s, %s, %s);",
                                     (uid, public_key, private_key))

                    _log.info(f'Successfully made new public-private key pair for uid {uid}')
                    return public_key
                else:
                    _log.info(f'UID {uid} already has an associated key, using that instead')
                    return row[1]
    except (Exception, psycopg2.Error) as error:
        _log.critical(f"Error while connecting to PostgreSQL: {error}")
        return None


def verify_jwt_with_public_key(json_web_token: str, public_key: bytes):
    """
    Decode a JWT with a public key.

    :param json_web_token: The JSON Web Token
    :param public_key: The public key casted to bytes
    :return: Decoded JWT if successful, jwt.exceptions.InvalidSignatureError if not
    """
    _log.info(f'Verifying JWT \"{json_web_token[:12]}...\"')
    return jwt.decode(jwt=json_web_token, key=public_key, algorithms='RS256')


if __name__ == '__main__':
    # Just code for testing authentication module
    _conn = psycopg2.connect(user="enriquevilla",
                             password=os.environ['DB_PASSWORD'],
                             host="localhost",
                             port="5432",
                             database="tapid")

    get_public_key_from_uid('4B 69 2D 0C', save_priv_key_on_new_uid=True, conn=_conn)
    # generate_key_pairs(to_database=True, conn=_conn, uid='4B 69 2D 0C')

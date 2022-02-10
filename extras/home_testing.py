import jwt
import psycopg2
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

uid = "00 00 00 00"
username = input("Enter your database username:\n")
password = input("Enter your database password:\n")
event_name = input("Enter your plug-ins event_name:\n")
jwt_password = input("Enter the password required to verify your JWT:\n")

conn = psycopg2.connect(user=username,
                        password=password,
                        host="localhost",
                        port="5432",
                        database="tapid")

curs = conn.cursor()

# 65537 as a public exponent is standard (e=3 is used sometimes, but a
# curious student can do future research on the security of this RSA implementation)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

print("Creating public-private key pair...")
# What's all this PEM, PKCS8, PKCS1 stuff?
# https://stackoverflow.com/questions/48958304/pkcs1-and-pkcs8-format-for-rsa-private-key
utf8_pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

utf8_pem_public_key = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.PKCS1
).decode('utf-8')

print("Inserting public key into database and private key in test database...")
curs.execute('insert into public_keys (uid, public_key) values (%s, %s);', (uid, utf8_pem_public_key))

# The dictionary we are encoding will contain student info for the server to verify
# It will get passed down to the run() function of an event
encoded = jwt.encode({"name": "Jane Doe", "grade": 1, "pass": jwt_password}, bytes(utf8_pem_private_key, 'utf-8'), algorithm="RS256")

print("\nPayload to send to the server:")
print(
    {
        "uid": "00 00 00 00",
        "event_name": event_name,
        "jwt": encoded,
        "event_data": {
            "test": "test"
        }
    }
)

conn.close()

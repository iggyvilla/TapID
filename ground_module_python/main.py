from machine import I2C, Pin, UART
from utils import parse_at_response, jwt_to_rfid_array, formatted_uid, ESP8266, writable_rfid_blocks, parse_ip_response
import utime
from sys import exit
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd

"""
LIBRARY 
"""

# To keep track of previous RFID card
previous_card = []

# MFRC522 reader class instantiation
reader = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)

# Instantiate I2C communications for LCD
i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# Instantiate UART communications with ESP8266
uart1 = UART(0, tx=Pin(12), rx=Pin(13), baudrate=115200, timeout=5000)
esp8266 = ESP8266(uart1, tx_pin=Pin(12), rx_pin=Pin(13))
print(uart1)

# TapAPI IP and port
SERVER_IP = "192.168.100.7"
SERVER_PORT = 8000


def clear_loading_screen(percent_done):
    """Function to easily set the loading screen without repeating code"""
    lcd.clear()
    # Think of move_to like moving where the type cursor is. That's exactly what it's doing!
    lcd.move_to(0, 0)
    lcd.putstr("TapID loading...")
    lcd.move_to(0, 1)
    percent_done = percent_done if percent_done <= 14 else 14
    lcd.putstr("[" + "=" * percent_done + " " * (14-percent_done) + "]")


def card_on_sensor_msg():
    """Function to easily put "enter card on sensor" message"""
    lcd.clear()
    lcd.putstr("Put card on")
    lcd.move_to(0, 1)
    lcd.putstr("sensor.")


# Test AT startup and see if ESP-01 is wired correctly
if esp8266.startup() is None:
    print("ESP8266 not setup properly")
    exit()

clear_loading_screen(2)

# Set the Wi-Fi mode to station mode (connects to WiFi instead of creating its own WiFi signal)
esp8266.wifi_mode(ESP8266.MODE_STATION)

clear_loading_screen(3)

# Connect to an AP
esp8266.connect_to_wifi("Akatsuki Hideout", "8prongedseal", timeout=6000)

clear_loading_screen(4)

# Get the modules IP address for metric use
resp = esp8266.get_local_ip_address()
module_ip = parse_ip_response(resp)

clear_loading_screen(8)

# Make sure we only connect to one network (the ESP-01 can connect to multiple networks)
esp8266.set_multiple_connections(False)

clear_loading_screen(10)

# Establish a TCP connection to the HTTP server
conn_resp = esp8266.establish_connection("TCP", SERVER_IP, SERVER_PORT)

# See if server is offline
if parse_at_response(conn_resp) == "ERROR\nCLOSED\n":
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Can't connect to")
    lcd.move_to(0, 1)
    lcd.putstr("TapID server.")
    exit()

# Make a GET request to TapAPI to see if the server is responsive
payload = esp8266.get(SERVER_IP, "/")

clear_loading_screen(12)

lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("API version:")
lcd.move_to(0, 1)
lcd.putstr(str(payload.body['api_version']))

utime.sleep(1)

print("SYSTEM INITIALIZATION COMPLETE\n\n")

card_on_sensor_msg()

while True:
    # Initialize the MFRC522 reader
    # Taken from example code from danjperron/micropython-mfrc522/Pico_examples/Pico_read.py
    reader.init()
    (stat, tag_type) = reader.request(reader.REQIDL)

    if stat == reader.OK:
        (stat, uid) = reader.SelectTagSN()

        if uid == previous_card:
            continue

        if stat == reader.OK:
            # Display that a card was detected
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr("Card detected")

            print(f"Card detected (uid={reader.tohexstring(uid)})")

            previous_card = uid

            # The default card key 0xFF six times
            # For testing purposes you can use it to reduce possible headaches
            # In deployment, write the key in the trailer sectors (where sector_n%4==3; 1,3,5,7...)
            defaultKey = [255, 255, 255, 255, 255, 255]

            # Function to read entire card, remove comment if needed
            # reader.MFRC522_DumpClassic1K(uid, Start=0, End=64, keyA=defaultKey)

            # Buffer for storing card information
            jwt_buf = []

            # Boolean to keep track if entire JWT was read
            read_complete = False

            # writable_rfid_blocks() are all blocks minus the trailer sectors)
            for block_num in writable_rfid_blocks():
                status = reader.auth(reader.AUTHENT1A, block_num, defaultKey, uid)
                end_of_text = False

                if status == reader.OK:
                    _status, read_block = reader.read(block_num)

                    if status == reader.OK:
                        for char in read_block:
                            # If we reach the end of text character (3 in decimal)
                            if char == 3:
                                end_of_text = True
                                read_complete = True
                                break
                            jwt_buf.append(chr(char))
                    else:
                        print("Error reading RFID card")
                else:
                    break

                if end_of_text:
                    break

            # If the end of text character wasn't read
            if not read_complete:
                print("Card not read completely, ignoring.")
                card_on_sensor_msg()
                continue

            # JWTs have two periods. This is the only not-so-resource-intensive way to
            # Check if there is a valid JWT
            if jwt_buf.count('.') != 2:
                print('Not a JWT. Ignoring card.')
                continue

            print(f"Read a JWT from RFID.")

            lcd.move_to(0, 1)
            lcd.putstr("Card read!")

            # A valid TapAPI payload
            payload = {
                "jwt": "".join(jwt_buf),
                "uid": formatted_uid(uid),
                "event_name": "borrow_book",
                "event_data": {
                    "book_id": 1,
                    "due_on": 7,
                    "save_to_google_docs": True
                }
            }

            print(payload)

            # Establish a TCP HTTP connection to the server ip and port
            esp8266.establish_connection(type="TCP", ip=SERVER_IP, port=SERVER_PORT)

            lcd.move_to(0, 1)
            lcd.putstr("Authenticating")

            # Perform the post request for authentication
            resp = esp8266.post(ip=SERVER_IP, route="/event", payload=payload)
            print("RECV:")
            print(resp)

            if not resp:
                lcd.clear()
                lcd.move_to(0, 0)
                lcd.putstr("Error. Try again.")
                utime.sleep(2)
                continue

            # If everything went well (200 OK)
            if resp.response_code == 200:
                # Display that everything went well to the user, you can do anything in this if statement
                lcd.clear()
                lcd.move_to(0, 0)
                lcd.putstr(f"Borrowed")
                lcd.move_to(0, 1)
                lcd.putstr(f"{resp.body['entry'][1]}")

            print("Done processing.\n")
        else:
            pass
    else:
        previous_card = []

    utime.sleep(1)

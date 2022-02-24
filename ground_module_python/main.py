from machine import I2C, Pin, UART
from utils import parse_http_payload, parse_at_response, jwt_to_rfid_array, formatted_uid, ESP8266
import utime
from sys import exit
import ujson
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd


def writable_rfid_blocks():
    return [z for z in range(1, 64) if (z % 4) != 3]


# To keep track of previous RFID card
previous_card = []

# Toggle between read/write modes
WRITE = False

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

SERVER_IP = "192.168.100.7"
SERVER_PORT = 8000


def clear_loading_screen(percent_done):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("TapID loading...")
    lcd.move_to(0, 1)
    percent_done = percent_done if percent_done <= 14 else 14
    lcd.putstr("[" + "=" * percent_done + " " * (14-percent_done) + "]")


def card_on_sensor_msg():
    lcd.clear()
    lcd.putstr("Put card on")
    lcd.move_to(0, 1)
    lcd.putstr("sensor.")


# Test AT startup
# esp8266_send('AT')
if esp8266.startup() is None:
    print("ESP8266 not setup properly")
    exit()

# esp8266_send('AT+GMR')      # Check version information
# esp8266_send('AT+CWMODE?')  # Query the Wi-Fi mode

clear_loading_screen(2)

# Set the Wi-Fi mode to station mode (connects to WiFi instead of creating its own WiFi signal)
esp8266.wifi_mode(ESP8266.MODE_STATION)

clear_loading_screen(3)

# esp8266_send('AT+CWLAP', timeout=10000)

# Connect to AP
esp8266.connect_to_wifi("Akatsuki Hideout", "8prongedseal", timeout=4000)

esp8266.get_local_ip_address()

esp8266.set_multiple_connections(False)

clear_loading_screen(6)

conn_resp = esp8266.establish_connection("TCP", SERVER_IP, SERVER_PORT)

if parse_at_response(conn_resp) == "ERROR\nCLOSED\n":
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Can't connect to")
    lcd.move_to(0, 1)
    lcd.putstr("TapID server.")
    exit()

# http_cmd = f"GET / HTTP/1.1\r\nHost: {SERVER_IP}\r\n\r\n"

# +12 because each \r\n count as 1 character
# esp8266_send(f'AT+CIPSEND={len(http_cmd) + 12}', timeout=1000)
# resp = esp8266_send(http_cmd, timeout=500)
payload = esp8266.get(SERVER_IP, "/")

clear_loading_screen(12)

utime.sleep(5)

lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("API version:")
lcd.move_to(0, 1)
lcd.putstr(str(payload.body['api_version']))

utime.sleep(1)

if WRITE:
    print("Ground Module in write mode. Writing JWT from jwts.txt")

print("SYSTEM INITIALIZATION COMPLETE\n\n")

card_on_sensor_msg()

while True:
    reader.init()
    (stat, tag_type) = reader.request(reader.REQIDL)

    if stat == reader.OK:
        (stat, uid) = reader.SelectTagSN()

        if uid == previous_card:
            continue

        if stat == reader.OK:
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr("Card detected")

            print(
                f"Card detected (uid={reader.tohexstring(uid)})")

            previous_card = uid

            # The default card key 0xFF six times
            # For testing purposes you can use it to reduce possible headaches
            # In deployment, write the key in the trailer sectors (where sector_n%4==3; 1,3,5,7...)
            defaultKey = [255, 255, 255, 255, 255, 255]

            # Function to read entire card
            # reader.MFRC522_DumpClassic1K(uid, Start=0, End=64, keyA=defaultKey)

            # If you want to use the ground module to write JWTs to cards
            if WRITE:
                jwt_arr = jwt_to_rfid_array("jwts.txt")
                print(jwt_arr)
                for x, block_num in enumerate(writable_rfid_blocks()):
                    print(f"{x=}")
                    status = reader.auth(reader.AUTHENT1A, block_num, defaultKey, uid)
                    if status == reader.OK:
                        try:
                            if x == 33:
                                print(jwt_arr)
                                print(jwt_arr[x])

                            status = reader.write(block_num, jwt_arr[x])
                            print(f"{jwt_arr[x]=}")
                            if status != reader.OK:
                                print("unable to write")
                                break
                        except IndexError:
                            break
                    else:
                        print("Authentication error for writing")
                        break

                    print(f"Block {block_num} success (#{x}).")

                print("Done writing.")

                exit()

            jwt_buf = []
            read_complete = False

            for block_num in writable_rfid_blocks():
                status = reader.auth(reader.AUTHENT1A, block_num, defaultKey, uid)
                end_of_text = False

                if status == reader.OK:
                    _status, read_block = reader.read(block_num)

                    if status == reader.OK:
                        for char in read_block:
                            # If we reach the end of text character
                            if char == 3:
                                end_of_text = True
                                read_complete = True
                                break
                            jwt_buf.append(chr(char))
                    else:
                        print("Error reading RFID card")

                if end_of_text:
                    break

            if not read_complete:
                print("Card not read completely, ignoring.")
                card_on_sensor_msg()
                continue

            if jwt_buf.count('.') != 2:
                print('Not a JWT. Ignoring card.')
                continue

            print(f"Read a JWT from RFID.")

            lcd.move_to(0, 1)
            lcd.putstr("Card read.")

            payload = {
                "jwt": "".join(jwt_buf),
                "uid": formatted_uid(uid),
                "event_name": "example_event",
                "event_data": {
                    "hello": "world",
                    "test": "data"
                }
            }

            print(payload)

            esp8266.establish_connection(type="TCP", ip=SERVER_IP, port=SERVER_PORT)

            resp = esp8266.post(ip=SERVER_IP, route="/event", payload=payload, timeout=1500)
            print("RECV:")
            print(resp)

            if resp.response_code == 200:
                lcd.clear()
                lcd.move_to(0, 0)
                lcd.putstr(f"Hello, G{resp.body['jwt_decoded']['grade']}")
                lcd.move_to(0, 1)
                lcd.putstr(resp.body['jwt_decoded']['name'].split(' ')[0])

            print("Done processing.\n")
        else:
            pass
    else:
        previous_card = []

    utime.sleep(1)

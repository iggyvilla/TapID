from machine import I2C, Pin, UART
from utils import parse_http_payload, parse_at_response, jwt_to_rfid_array, formatted_uid
import utime
from sys import exit
import ujson
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd


def writable_rfid_blocks():
    return [z for z in range(1, 64) if (z % 4) != 3]


# To keep track of previous RFID card
previous_card = []

# Enable write access
WRITE = False

# MFRC522 reader class instantiation
reader = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)


# Instantiate I2C communications for LCD
i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# Instantiate UART communications
uart1 = UART(0, tx=Pin(12), rx=Pin(13), baudrate=115200, timeout=10000)
print(uart1)

SERVER_IP = "192.168.100.7"
SERVER_PORT = 8000


def change_uart_timeout(timeout: int):
    global uart1
    uart1 = UART(0, tx=Pin(12), rx=Pin(13), baudrate=115200, timeout=timeout)


def esp8266_send(cmd, timeout=1000):
    global uart1
    print("CMD: " + cmd)
    uart1 = UART(0, tx=Pin(12), rx=Pin(13), baudrate=115200, timeout=timeout)
    uart1.write(cmd+'\r\n')
    _resp = uart1.read()

    print("resp:")
    try:
        print(_resp.decode())
        return _resp.decode()
    except UnicodeError:
        print(_resp)
        return _resp
    except AttributeError:
        print('Retrying previous command (RESP: ' + str(_resp).replace("\r\n", " ") + ')')
        return esp8266_send(cmd, timeout=timeout)


def esp8266_request(_payload, timeout=1000):
    global uart1
    print("CMD: " + cmd)
    uart1 = UART(0, tx=Pin(12), rx=Pin(13), baudrate=115200, timeout=timeout)
    uart1.write(cmd + '\r\n')
    _resp = uart1.read()
    print(str(_resp))

    all_ok = False

    while not all_ok:
        uart1.write("AT" + '\r\n')
        _resp = uart1.read().decode()
        print("Busy...")
        if "OK" in _resp:
            print(f"OK ({_resp})")
            all_ok = True
            return esp8266_send(_payload, timeout=timeout)
        utime.sleep(1)


def clear_loading_screen(percent_done):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("TapID loading...")
    lcd.move_to(0, 1)
    percent_done = percent_done if percent_done <= 14 else 14
    lcd.putstr("[" + "=" * percent_done + " " * (14-percent_done) + "]")


# Test AT startup
esp8266_send('AT')
# esp8266_send('AT+GMR')      # Check version information
# esp8266_send('AT+CWMODE?')  # Query the Wi-Fi mode

clear_loading_screen(2)

# Set the Wi-Fi mode to station mode (connects to WiFi instead of creating its own WiFi signal)
esp8266_send('AT+CWMODE=1')

clear_loading_screen(3)

# esp8266_send('AT+CWLAP', timeout=10000)      # List available APs

# Connect to AP
esp8266_send('AT+CWJAP="Akatsuki Hideout","8prongedseal"', timeout=4000)
esp8266_send('AT+CIFSR')      # Obtain the Local IP Address
esp8266_send('AT+CIPMUX=0')   # Set to just one connection
clear_loading_screen(6)
conn_resp = esp8266_send(f'AT+CIPSTART="TCP","{SERVER_IP}",{SERVER_PORT}', timeout=2000)

if parse_at_response(conn_resp) == "ERROR\nCLOSED\n":
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Can't connect to")
    lcd.move_to(0, 1)
    lcd.putstr("TapID server.")
    exit()

http_cmd = f"GET / HTTP/1.1\r\nHost: {SERVER_IP}\r\n\r\n"

# +12 because each \r\n count as 1 character
esp8266_send(f'AT+CIPSEND={len(http_cmd) + 12}', timeout=1000)
resp = esp8266_send(http_cmd, timeout=500)
payload = parse_http_payload(resp)

clear_loading_screen(12)

utime.sleep(5)

lcd.clear()
lcd.move_to(0, 0)
lcd.putstr("API version:")
lcd.move_to(0, 1)
lcd.putstr(str(payload['json']['api_version']))

utime.sleep(1)

if WRITE:
    print("Write mode. Writing JWT in jwts.txt")

while True:
    reader.init()
    (stat, tag_type) = reader.request(reader.REQIDL)

    if stat == reader.OK:
        (stat, uid) = reader.SelectTagSN()

        if uid == previous_card:
            continue

        if stat == reader.OK:
            print(
                f"Card detected {hex(int.from_bytes(bytes(uid), 'little', False)).upper()} uid={reader.tohexstring(uid)}")

            previous_card = uid

            # The default card key 0xFF six times
            # For test purposes, we use this to reduce complexity
            defaultKey = [255, 255, 255, 255, 255, 255]

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

            jwt = []

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
                                break
                            jwt.append(chr(char))
                    else:
                        print("Error reading RFID card")

                if end_of_text:
                    break

            if jwt.count('.') != 2:
                print('Not a JWT. Ignoring card.')
                continue

            print(f"Read a JWT from RFID.")

            payload = {
                "jwt": "".join(jwt),
                "uid": formatted_uid(uid),
                "event_name": "example_event",
                "event_data": {
                    "hello": "world",
                    "test": "data"
                }
            }

            print(payload)
            conn_resp = esp8266_send(f'AT+CIPSTART="TCP","{SERVER_IP}",{SERVER_PORT}', timeout=2000)

            # cmd = f"POST /event HTTP/1.1\r\nHost: {SERVER_IP}\r\nContent-Type: application/json\r\nContent-Length: {len(str(payload))}\r\n\r\n{ujson.dumps(payload)}\r\n\r\n"
            # \r\nAccept-Encoding: gzip, deflate\r\nAccept: */*\r\nContent-Type: application/json\r\n

            json_str = ujson.dumps(payload)
            cmd = f'POST /event HTTP/1.1\r\nHost: 192.168.100.7\r\nContent-Type: application/json\r\nContent-Length: {len(json_str)}\r\n\r\n{json_str}\r\n'
            esp8266_send(f'AT+CIPSEND={len(cmd) + 24}', timeout=2000)

            # uart1.write(cmd + "\r\n")

            esp8266_send(cmd)

            change_uart_timeout(1000)

            response_ok = False
            while not response_ok:
                uart1.write("AT\r\n")
                _resp = uart1.read()

                if _resp is None:
                    continue
                else:
                    print(_resp.decode())
                    response_ok = True

            print("Done")
        else:
            pass
    else:
        previous_card = []

    utime.sleep(1)

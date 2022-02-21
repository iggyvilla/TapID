from machine import I2C, Pin, UART
import utime
from esp8266 import ESP8266
# from pico_i2c_lcd import I2cLcd

# led = Pin(25, Pin.OUT)
#
# i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=400000)
# I2C_ADDR = i2c.scan()[0]
# lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# uart1 = UART(1, tx=Pin(8), rx=Pin(9), baudrate=115200, timeout=5000)
# print(uart1)

esp01 = ESP8266()
esp8266_at_ver = None

print("StartUP", esp01.startUP())

if esp8266_at_var := esp01.getVersion():
    print(esp8266_at_var)


# def sendCMD_waitResp(cmd, uart=uart1, timeout=2000):
#     print("CMD: " + cmd)
#     uart.write(cmd)
#     waitResp(uart, timeout)
#     print()


# def waitResp(uart=uart1, timeout=2000):
#     prvMills = utime.ticks_ms()
#     # resp = b""
#     resp = uart.read()
#     # while (utime.ticks_ms() - prvMills) < timeout:
#     #     if uart.any():
#     #         resp = b"".join([resp, uart.read(1)])
#     #     resp = uart.read()
#     print("resp:")
#     try:
#         print(resp.decode())
#     except UnicodeError:
#         print(resp)


# Test AT startup
# sendCMD_waitResp('AT\r\n')            # Test AT startup
# sendCMD_waitResp('AT+GMR\r\n')        # Check version information
# sendCMD_waitResp('AT+CWMODE?\r\n')  # Query the Wi-Fi mode
# sendCMD_waitResp('AT+CWMODE=1\r\n') # Set the Wi-Fi mode = Station mode
# sendCMD_waitResp('AT+CWMODE?\r\n')  # Query the Wi-Fi mode again
# sendCMD_waitResp('AT+CWLAP\r\n')      # List available APs
# sendCMD_waitResp('AT+CWJAP="ssid","password"\r\n', timeout=5000) #Connect to AP
# sendCMD_waitResp('AT+CIFSR\r\n')    #Obtain the Local IP Address

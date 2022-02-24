import ujson
from machine import UART


def parse_http_payload(raw_payload: str) -> dict:
    """Parses raw HTTP payload from the ESP8266 into an organized dictionary"""
    raw_payload = raw_payload.replace("\r", "")
    split = raw_payload[raw_payload.find("SEND OK") + len("SEND OK") + 1:raw_payload.find("CLOSED")].split("\n\n")
    _split = [x.split(": ") for x in split[0].split("\n") if x.split(": ")[0] != '']
    _response_code = _split[0][0].split(" ")[1]
    _final = {key: value for key, value in _split[1:]}
    _final["response_code"] = _response_code
    _final["json"] = ujson.loads(split[1])
    return _final


def parse_at_response(resp: str):
    return resp.replace("\r", "").split("\n\n")[1]


def jwt_to_rfid_array(filename: str):
    """Read a JWT (single line) in a text file on the root dir"""
    jwt_str = open(filename, 'r').readline()
    print(jwt_str)
    split_arr = [jwt_str[i:i+16] for i in range(0, len(jwt_str), 16)]
    eot_appended = False
    out_arr = []

    if len(split_arr) > 47:
        return ValueError("JWT too big for 1K MIFARE card")

    for sector in split_arr:
        z = []

        for ch in sector:
            z.append(ord(ch))

        if len(z) < 16:
            # Append 3 to indicate end of text in ASCII
            z.append(3)
            z = z + [0] * (16 - len(z))
            eot_appended = True

        out_arr.append(z)

    if not eot_appended:
        out_arr.append([3] + [0] * 15)

    return out_arr


def formatted_uid(raw_uid: list):
    out = []

    for z in raw_uid:
        char = str(hex(z))[2:].upper()
        if z < 0x10:
            out.append("0"+char)
            continue
        out.append(char)

    return " ".join(out)


class Response:
    def __init__(self, headers, body):
        self.headers = headers
        self.body = body
        self.response_code = int(headers['response_code'])

    def __repr__(self):
        return f"Response(\n    headers={self.headers}\n    body={self.body}\n)"


# TX = 12, RX = 13
class ESP8266:

    MODE_NULL = 0
    MODE_STATION = 1
    MODE_SOFT_AP = 2
    MODE_SOFTAP_STATION = 3

    def __init__(self, uart: UART, tx_pin, rx_pin):
        self.uart = uart
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin

    def change_uart_timeout(self, timeout=1000):
        self.uart = UART(0, tx=self.tx_pin, rx=self.rx_pin, baudrate=115200, timeout=timeout)

    def send(self, cmd, timeout=1000):
        print("CMD: " + cmd)
        self.uart = UART(0, tx=self.tx_pin, rx=self.rx_pin, baudrate=115200, timeout=timeout)
        self.uart.write(cmd+'\r\n')
        _resp = self.uart.read()

        print("resp:")
        try:
            print(_resp.decode())
            return _resp.decode()
        except UnicodeError:
            print(_resp)
            return _resp
        except AttributeError:
            print('Retrying previous command (RESP: ' + str(_resp).replace("\r\n", " ") + ')')
            return self.send(cmd, timeout=timeout)

    def startup(self, timeout=1000):
        return self.send('AT', timeout=timeout)

    def wifi_mode(self, mode: int, timeout=1000):
        """
        Set the ESP8266s mode (you can use ESP8266.MODE_ properties)

        :param timeout:
        :param mode: Mode to set to
         (0: Null mode. Wi-Fi RF will be disabled.
          1: Station mode.
          2: SoftAP mode.
          3: SoftAP+Station mode.
        :return:
        """
        return self.send(f'AT+CWMODE={mode}', timeout=timeout)

    def connect_to_wifi(self, ssid: str, password: str, timeout=1000):
        """
        Connect to a WAP.

        :param timeout:
        :param ssid: The network's name
        :param password: The network's password
        :return:
        """
        return self.send(f'AT+CWJAP="{ssid}","{password}"', timeout=timeout)

    def get_local_ip_address(self, timeout=1000):
        return self.send('AT+CIFSR', timeout=timeout)

    def set_multiple_connections(self, z: bool, timeout=1000):
        return self.send(f'AT+CIPMUX={int(z)}', timeout=timeout)

    def establish_connection(self, type: str, ip: str, port: int, timeout=1000):
        """
        Establish a TCP/UDP connection to a remote host.

        :param timeout:
        :param type: "TCP"/"UDP"
        :param ip: The IP address of your server
        :param port: The port of your server
        :return:
        """
        return self.send(f'AT+CIPSTART="{type}","{ip}",{port}', timeout=timeout)

    def get(self, ip: str, route: str, timeout=1000):
        """
        Do an HTTP GET request

        :param ip: The IP address of your server
        :param route: Where the request will happen (ex. if you want 127.0.0.1/home, put "/home")
        :return:
        """
        cmd = f"GET {route} HTTP/1.1\r\nHost: {ip}\r\n\r\n"
        self.send(f'AT+CIPSEND=' + str(len(cmd) + cmd.count("\r\n") * 4))
        self.change_uart_timeout(500)
        self.uart.write(cmd + "\r\n")
        while True:
            self.uart.write("AT\r\n")
            _resp = self.uart.read()

            if _resp is None:
                continue
            else:
                decode = _resp.decode()
                parsed = parse_http_payload(decode[decode.find("+IPD"):])
                body = parsed.pop('json')

                return Response(body=body, headers=parsed)

    def post(self, ip: str, route: str, payload: dict, timeout=1000) -> Response:
        """
        Do an HTTP POST request

        :param timeout: Time before UART timeout
        :param payload: dict of your JSON payload
        :param ip: The IP address of your server
        :param route: Where the request will happen (ex. if you want 127.0.0.1/home, put "/home")
        :return: Response
        """
        json_str = ujson.dumps(payload)
        cmd = f"POST {route} HTTP/1.1\r\nHost: {ip}\r\nContent-Type: application/json\r\nContent-Length: {len(json_str)}\r\n\r\n{json_str}\r\n"
        self.send(f'AT+CIPSEND=' + str(len(cmd) + cmd.count("\r\n")*4))
        self.change_uart_timeout(500)
        self.uart.write(cmd + "\r\n")
        while True:
            self.uart.write("AT\r\n")
            _resp = self.uart.read()

            if _resp is None:
                continue
            else:
                decode = _resp.decode()
                parsed = parse_http_payload(decode[decode.find("+IPD"):])
                body = parsed.pop('json')

                return Response(body=body, headers=parsed)

import ujson


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

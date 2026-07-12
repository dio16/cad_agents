def json_parse(s: str) -> object:
    if not isinstance(s, str):
        raise ValueError("Input must be a string")

    pos = [0]
    length = len(s)

    def skip_whitespace():
        while pos[0] < length and s[pos[0]] in ' \t\n\r':
            pos[0] += 1

    def peek():
        skip_whitespace()
        if pos[0] < length:
            return s[pos[0]]
        return None

    def advance():
        pos[0] += 1

    def expect(ch):
        skip_whitespace()
        if pos[0] >= length or s[pos[0]] != ch:
            raise ValueError(f"Expected '{ch}' at position {pos[0]}")
        pos[0] += 1

    def parse_value():
        skip_whitespace()
        if pos[0] >= length:
            raise ValueError("Unexpected end of input")

        ch = s[pos[0]]

        if ch == '"':
            return parse_string()
        elif ch == '{':
            return parse_object()
        elif ch == '[':
            return parse_array()
        elif ch == 't':
            return parse_true()
        elif ch == 'f':
            return parse_false()
        elif ch == 'n':
            return parse_null()
        elif ch == '-' or ch.isdigit():
            return parse_number()
        else:
            raise ValueError(f"Unexpected character '{ch}' at position {pos[0]}")

    def parse_string():
        expect('"')
        chars = []
        while pos[0] < length:
            ch = s[pos[0]]
            if ch == '"':
                pos[0] += 1
                return ''.join(chars)
            elif ch == '\\':
                pos[0] += 1
                if pos[0] >= length:
                    raise ValueError("Unterminated string escape")
                esc = s[pos[0]]
                if esc == '"':
                    chars.append('"')
                elif esc == '\\':
                    chars.append('\\')
                elif esc == '/':
                    chars.append('/')
                elif esc == 'b':
                    chars.append('\b')
                elif esc == 'f':
                    chars.append('\f')
                elif esc == 'n':
                    chars.append('\n')
                elif esc == 'r':
                    chars.append('\r')
                elif esc == 't':
                    chars.append('\t')
                elif esc == 'u':
                    pos[0] += 1
                    hex_str = s[pos[0]:pos[0]+4]
                    if len(hex_str) < 4:
                        raise ValueError("Incomplete unicode escape")
                    try:
                        code_point = int(hex_str, 16)
                    except ValueError:
                        raise ValueError(f"Invalid unicode escape: \\u{hex_str}")
                    pos[0] += 3

                    if 0xD800 <= code_point <= 0xDBFF:
                        if pos[0] + 1 >= length or s[pos[0]+1] != '\\' or s[pos[0]+2] != 'u':
                            raise ValueError("Lone high surrogate")
                        pos[0] += 3
                        hex_str2 = s[pos[0]:pos[0]+4]
                        if len(hex_str2) < 4:
                            raise ValueError("Incomplete low surrogate")
                        try:
                            low = int(hex_str2, 16)
                        except ValueError:
                            raise ValueError(f"Invalid low surrogate: \\u{hex_str2}")
                        if not (0xDC00 <= low <= 0xDFFF):
                            raise ValueError("Invalid low surrogate")
                        pos[0] += 3
                        code_point = 0x10000 + (code_point - 0xD800) * 0x400 + (low - 0xDC00)
                    elif 0xDC00 <= code_point <= 0xDFFF:
                        raise ValueError("Lone low surrogate")

                    chars.append(chr(code_point))
                else:
                    raise ValueError(f"Invalid escape character: \\{esc}")
                pos[0] += 1
            elif ord(ch) < 0x20:
                raise ValueError(f"Unescaped control character in string at position {pos[0]}")
            else:
                chars.append(ch)
                pos[0] += 1

        raise ValueError("Unterminated string")

    def parse_number():
        start = pos[0]
        if s[pos[0]] == '-':
            pos[0] += 1

        if pos[0] >= length or not s[pos[0]].isdigit():
            raise ValueError(f"Invalid number at position {start}")

        if s[pos[0]] == '0':
            pos[0] += 1
            if pos[0] < length and s[pos[0]].isdigit():
                raise ValueError(f"Leading zeros not allowed at position {start}")
        else:
            while pos[0] < length and s[pos[0]].isdigit():
                pos[0] += 1

        is_float = False

        if pos[0] < length and s[pos[0]] == '.':
            is_float = True
            pos[0] += 1
            if pos[0] >= length or not s[pos[0]].isdigit():
                raise ValueError(f"Invalid number: no digits after decimal point at position {start}")
            while pos[0] < length and s[pos[0]].isdigit():
                pos[0] += 1

        if pos[0] < length and s[pos[0]] in 'eE':
            is_float = True
            pos[0] += 1
            if pos[0] < length and s[pos[0]] in '+-':
                pos[0] += 1
            if pos[0] >= length or not s[pos[0]].isdigit():
                raise ValueError(f"Invalid number: no digits in exponent at position {start}")
            while pos[0] < length and s[pos[0]].isdigit():
                pos[0] += 1

        num_str = s[start:pos[0]]

        if is_float:
            return float(num_str)
        else:
            return int(num_str)

    def parse_object():
        expect('{')
        obj = {}

        if peek() == '}':
            pos[0] += 1
            return obj

        while True:
            if peek() != '"':
                raise ValueError(f"Expected string key at position {pos[0]}")
            key = parse_string()

            expect(':')
            value = parse_value()
            obj[key] = value

            ch = peek()
            if ch == '}':
                pos[0] += 1
                return obj
            elif ch == ',':
                pos[0] += 1
                if peek() == '}':
                    raise ValueError("Trailing comma in object")
            else:
                raise ValueError(f"Expected ',' or '}}' in object at position {pos[0]}")

    def parse_array():
        expect('[')
        arr = []

        if peek() == ']':
            pos[0] += 1
            return arr

        while True:
            value = parse_value()
            arr.append(value)

            ch = peek()
            if ch == ']':
                pos[0] += 1
                return arr
            elif ch == ',':
                pos[0] += 1
                if peek() == ']':
                    raise ValueError("Trailing comma in array")
            else:
                raise ValueError(f"Expected ',' or ']' in array at position {pos[0]}")

    def parse_true():
        if s[pos[0]:pos[0]+4] != 'true':
            raise ValueError(f"Invalid value at position {pos[0]}")
        pos[0] += 4
        return True

    def parse_false():
        if s[pos[0]:pos[0]+5] != 'false':
            raise ValueError(f"Invalid value at position {pos[0]}")
        pos[0] += 5
        return False

    def parse_null():
        if s[pos[0]:pos[0]+4] != 'null':
            raise ValueError(f"Invalid value at position {pos[0]}")
        pos[0] += 4
        return None

    result = parse_value()

    skip_whitespace()
    if pos[0] < length:
        raise ValueError(f"Extra characters after JSON at position {pos[0]}")

    return result

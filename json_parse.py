def json_parse(s: str) -> object:
    i = 0
    n = len(s)

    _WS = frozenset(' \t\n\r')

    def _skip_ws():
        nonlocal i
        while i < n and s[i] in _WS:
            i += 1

    def _peek():
        return s[i] if i < n else ''

    def _expect(ch):
        nonlocal i
        if i >= n or s[i] != ch:
            raise ValueError(f"Expected {ch!r}")
        i += 1

    def _parse_string():
        nonlocal i
        _expect('"')
        chunks = []
        while i < n:
            ch = s[i]
            if ch == '"':
                i += 1
                return ''.join(chunks)
            if ch == '\\':
                i += 1
                if i >= n:
                    raise ValueError("Unterminated string escape")
                esc = s[i]
                i += 1
                if esc == '"':
                    chunks.append('"')
                elif esc == '\\':
                    chunks.append('\\')
                elif esc == '/':
                    chunks.append('/')
                elif esc == 'b':
                    chunks.append('\b')
                elif esc == 'f':
                    chunks.append('\f')
                elif esc == 'n':
                    chunks.append('\n')
                elif esc == 'r':
                    chunks.append('\r')
                elif esc == 't':
                    chunks.append('\t')
                elif esc == 'u':
                    if i + 4 > n:
                        raise ValueError("Unterminated \\u escape")
                    hi = s[i:i+4]
                    if not all(c in '0123456789abcdefABCDEF' for c in hi):
                        raise ValueError(f"Invalid hex in \\u escape: {hi}")
                    code = int(hi, 16)
                    i += 4
                    if 0xD800 <= code <= 0xDBFF:
                        if not (i + 2 <= n and s[i] == '\\' and s[i+1] == 'u'):
                            raise ValueError(f"Lone high surrogate \\u{hi}")
                        if i + 6 > n:
                            raise ValueError("Unterminated surrogate pair")
                        lo_hex = s[i+2:i+6]
                        if not all(c in '0123456789abcdefABCDEF' for c in lo_hex):
                            raise ValueError(f"Invalid hex in surrogate pair: {lo_hex}")
                        lo = int(lo_hex, 16)
                        if not (0xDC00 <= lo <= 0xDFFF):
                            raise ValueError(f"High surrogate \\u{hi} not followed by low surrogate")
                        i += 6
                        code = 0x10000 + (code - 0xD800) * 0x400 + (lo - 0xDC00)
                    elif 0xDC00 <= code <= 0xDFFF:
                        raise ValueError(f"Lone low surrogate \\u{hi}")
                    chunks.append(chr(code))
                else:
                    raise ValueError(f"Invalid escape: \\{esc}")
            elif ch < ' ':
                raise ValueError("Unescaped control character in string")
            else:
                chunks.append(ch)
                i += 1
        raise ValueError("Unterminated string")

    def _parse_number():
        nonlocal i
        start = i
        if _peek() == '-':
            i += 1

        if i >= n:
            raise ValueError("Incomplete number")

        if _peek() == '0':
            i += 1
        elif '1' <= _peek() <= '9':
            while i < n and '0' <= _peek() <= '9':
                i += 1
        else:
            raise ValueError(f"Invalid number")

        if _peek() == '.':
            i += 1
            if i >= n or not ('0' <= _peek() <= '9'):
                raise ValueError("Malformed number: trailing decimal point")
            while i < n and '0' <= _peek() <= '9':
                i += 1

        if i < n and _peek() in 'eE':
            i += 1
            if i < n and _peek() in '+-':
                i += 1
            if i >= n or not ('0' <= _peek() <= '9'):
                raise ValueError("Malformed number: incomplete exponent")
            while i < n and '0' <= _peek() <= '9':
                i += 1

        num = s[start:i]
        try:
            if '.' in num or 'e' in num or 'E' in num:
                return float(num)
            return int(num)
        except ValueError:
            raise ValueError(f"Invalid number: {num}")

    def _parse_value():
        nonlocal i
        _skip_ws()
        if i >= n:
            raise ValueError("Unexpected end of input")
        ch = _peek()
        if ch == '{':
            return _parse_object()
        if ch == '[':
            return _parse_array()
        if ch == '"':
            return _parse_string()
        if ch == 't':
            if s[i:i+4] == 'true':
                i += 4
                return True
            raise ValueError("Invalid token")
        if ch == 'f':
            if s[i:i+5] == 'false':
                i += 5
                return False
            raise ValueError("Invalid token")
        if ch == 'n':
            if s[i:i+4] == 'null':
                i += 4
                return None
            raise ValueError("Invalid token")
        if ch == '-' or '0' <= ch <= '9':
            return _parse_number()
        raise ValueError(f"Unexpected character: {ch!r}")

    def _parse_object():
        nonlocal i
        _expect('{')
        _skip_ws()
        if _peek() == '}':
            i += 1
            return {}

        result = {}
        while True:
            _skip_ws()
            key = _parse_string()
            _skip_ws()
            _expect(':')
            result[key] = _parse_value()
            _skip_ws()
            if _peek() == '}':
                i += 1
                return result
            _expect(',')
            _skip_ws()
            if _peek() == '}':
                raise ValueError("Trailing comma in object")

    def _parse_array():
        nonlocal i
        _expect('[')
        _skip_ws()
        if _peek() == ']':
            i += 1
            return []

        result = []
        while True:
            result.append(_parse_value())
            _skip_ws()
            if _peek() == ']':
                i += 1
                return result
            _expect(',')
            _skip_ws()
            if _peek() == ']':
                raise ValueError("Trailing comma in array")

    _skip_ws()
    value = _parse_value()
    _skip_ws()
    if i < n:
        raise ValueError(f"Unexpected trailing characters at position {i}")
    return value

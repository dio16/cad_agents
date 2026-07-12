def utf8_encode(codepoints: list[int]) -> bytes:
    result = bytearray()
    for cp in codepoints:
        if cp < 0 or cp > 0x10FFFF:
            raise ValueError(f"Invalid code point: {cp:#x}")
        if 0xD800 <= cp <= 0xDFFF:
            raise ValueError(f"Surrogate code point: {cp:#x}")
        if cp <= 0x7F:
            result.append(cp)
        elif cp <= 0x7FF:
            result.append(0xC0 | (cp >> 6))
            result.append(0x80 | (cp & 0x3F))
        elif cp <= 0xFFFF:
            result.append(0xE0 | (cp >> 12))
            result.append(0x80 | ((cp >> 6) & 0x3F))
            result.append(0x80 | (cp & 0x3F))
        else:
            result.append(0xF0 | (cp >> 18))
            result.append(0x80 | ((cp >> 12) & 0x3F))
            result.append(0x80 | ((cp >> 6) & 0x3F))
            result.append(0x80 | (cp & 0x3F))
    return bytes(result)


def utf8_decode(data: bytes) -> list[int]:
    result = []
    i = 0
    n = len(data)
    while i < n:
        b0 = data[i]
        if b0 <= 0x7F:
            cp = b0
            i += 1
        elif 0xC2 <= b0 <= 0xDF:
            if i + 1 >= n:
                raise ValueError("Truncated sequence at end of data")
            b1 = data[i + 1]
            if (b1 & 0xC0) != 0x80:
                raise ValueError(f"Invalid continuation byte: {b1:#x}")
            cp = ((b0 & 0x1F) << 6) | (b1 & 0x3F)
            i += 2
        elif (b0 & 0xF0) == 0xE0:
            if i + 2 >= n:
                raise ValueError("Truncated sequence at end of data")
            b1 = data[i + 1]
            b2 = data[i + 2]
            if (b1 & 0xC0) != 0x80 or (b2 & 0xC0) != 0x80:
                raise ValueError("Invalid continuation byte")
            cp = ((b0 & 0x0F) << 12) | ((b1 & 0x3F) << 6) | (b2 & 0x3F)
            if cp < 0x800:
                raise ValueError(f"Overlong encoding: {cp:#x}")
            i += 3
        elif (b0 & 0xF8) == 0xF0:
            if i + 3 >= n:
                raise ValueError("Truncated sequence at end of data")
            b1 = data[i + 1]
            b2 = data[i + 2]
            b3 = data[i + 3]
            if (b1 & 0xC0) != 0x80 or (b2 & 0xC0) != 0x80 or (b3 & 0xC0) != 0x80:
                raise ValueError("Invalid continuation byte")
            cp = ((b0 & 0x07) << 18) | ((b1 & 0x3F) << 12) | ((b2 & 0x3F) << 6) | (b3 & 0x3F)
            if cp < 0x10000:
                raise ValueError(f"Overlong encoding: {cp:#x}")
            i += 4
        else:
            raise ValueError(f"Invalid lead byte: {b0:#x}")
        if 0xD800 <= cp <= 0xDFFF:
            raise ValueError(f"Surrogate code point: {cp:#x}")
        if cp > 0x10FFFF:
            raise ValueError(f"Code point out of range: {cp:#x}")
        result.append(cp)
    return result

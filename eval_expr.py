def eval_expr(s: str) -> float:
    """Evaluate an arithmetic expression and return the result as float."""
    pos = 0
    tokens = []
    while pos < len(s):
        c = s[pos]
        if c.isspace():
            pos += 1
        elif c in "+-*/()":
            tokens.append(c)
            pos += 1
        elif c.isdigit() or c == '.':
            start = pos
            has_dot = c == '.'
            pos += 1
            while pos < len(s) and (s[pos].isdigit() or (s[pos] == '.' and not has_dot)):
                if s[pos] == '.':
                    has_dot = True
                pos += 1
            tokens.append(float(s[start:pos]))
        else:
            raise ValueError(f"Unexpected character: {c}")

    idx = 0

    def peek():
        nonlocal idx
        return tokens[idx] if idx < len(tokens) else None

    def consume():
        nonlocal idx
        t = tokens[idx]
        idx += 1
        return t

    def parse_expr():
        left = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            left = left + right if op == '+' else left - right
        return left

    def parse_term():
        left = parse_factor()
        while peek() in ('*', '/'):
            op = consume()
            right = parse_factor()
            if op == '/':
                left = left / right
            else:
                left = left * right
        return left

    def parse_factor():
        t = peek()
        if t == '(':
            consume()
            val = parse_expr()
            if consume() != ')':
                raise ValueError("Missing closing parenthesis")
            return val
        if t == '-':
            consume()
            return -parse_factor()
        if t == '+':
            consume()
            return parse_factor()
        return consume()

    result = parse_expr()
    return float(result)

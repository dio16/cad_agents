def query(rows: list[dict], where: str) -> list[dict]:
    """Return rows (in original order) whose fields satisfy `where`."""
    import re

    where = where.strip()

    # ── Lexer ──────────────────────────────────────────────────────────
    TOKEN_RE = re.compile(r"""
        \s*
        (?:
            (?P<OP>!=|>=|<=|>|<|=)
          | (?P<OR>OR\b)
          | (?P<AND>AND\b)
          | (?P<LIKE>LIKE\b)
          | (?P<TRUE>TRUE\b)
          | (?P<FALSE>FALSE\b)
          | (?P<NULL>NULL\b)
          | (?P<NUM>\d+(?:\.\d+)?)
          | (?P<DQS>"(?:[^"\\]|\\.)*")
          | (?P<SQS>'(?:[^'\\]|\\.)*')
          | (?P<COL>[a-zA-Z_][a-zA-Z0-9_]*)
        )
    """, re.VERBOSE)

    tokens = []
    pos = 0
    while pos < len(where):
        m = TOKEN_RE.match(where, pos)
        if not m:
            raise ValueError(f"Unexpected character at position {pos}")
        kind = m.lastgroup
        value = m.group(kind)
        if kind == 'OP':
            tokens.append(('OP', value))
        elif kind == 'OR':
            tokens.append(('OR', None))
        elif kind == 'AND':
            tokens.append(('AND', None))
        elif kind == 'LIKE':
            tokens.append(('LIKE', None))
        elif kind == 'TRUE':
            tokens.append(('BOOL', True))
        elif kind == 'FALSE':
            tokens.append(('BOOL', False))
        elif kind == 'NULL':
            tokens.append(('NULL', None))
        elif kind == 'NUM':
            tokens.append(('NUM', float(value) if '.' in value else int(value)))
        elif kind == 'DQS':
            s = value[1:-1]
            s = s.replace('\\"', '"').replace('\\\\', '\\')
            tokens.append(('STR', s))
        elif kind == 'SQS':
            s = value[1:-1]
            s = s.replace("\\'", "'").replace('\\\\', '\\')
            tokens.append(('STR', s))
        elif kind == 'COL':
            tokens.append(('COL', value))
        pos = m.end()

    tokens.append(('EOF', None))

    # ── Predicate helpers ──────────────────────────────────────────────
    def _is_num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    def _eq(lhs, val):
        if lhs is None and val is None:
            return True
        if lhs is None or val is None:
            return False
        if _is_num(lhs) and _is_num(val):
            return lhs == val
        if isinstance(lhs, str) and isinstance(val, str):
            return lhs == val
        if type(lhs) is type(val):
            return lhs == val
        return False

    def _make_cmp(col, op, val):
        def pred(row):
            if col not in row:
                raise ValueError(f"Unknown column: {col}")
            lhs = row[col]
            if op == '=':
                return _eq(lhs, val)
            if op == '!=':
                return not _eq(lhs, val)
            # > >= < <=
            if lhs is None or val is None:
                return False
            if not (_is_num(lhs) and _is_num(val)):
                return False
            if op == '>':
                return lhs > val
            if op == '>=':
                return lhs >= val
            if op == '<':
                return lhs < val
            if op == '<=':
                return lhs <= val
            return False
        return pred

    def _make_like(col, pattern):
        parts = []
        for ch in pattern:
            if ch == '%':
                parts.append('.*')
            elif ch == '_':
                parts.append('.')
            elif ch in '.^$*+?{}[]\\|()':
                parts.append('\\' + ch)
            else:
                parts.append(ch)
        regex = re.compile('^' + ''.join(parts) + '$')

        def pred(row):
            if col not in row:
                raise ValueError(f"Unknown column: {col}")
            lhs = row[col]
            if not isinstance(lhs, str):
                return False
            return bool(regex.match(lhs))
        return pred

    # ── Recursive-descent parser ───────────────────────────────────────
    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.i = 0

        def peek(self):
            return self.tokens[self.i]

        def advance(self):
            tok = self.tokens[self.i]
            self.i += 1
            return tok

        def expect(self, kind):
            tok = self.advance()
            if tok[0] != kind:
                raise ValueError(f"Expected {kind}, got {tok[0]}")
            return tok

        def parse(self):
            pred = self.parse_or()
            if self.peek()[0] != 'EOF':
                raise ValueError(f"Unexpected token: {self.peek()[0]}")
            return pred

        def parse_or(self):
            left = self.parse_and()
            while self.peek()[0] == 'OR':
                self.advance()
                right = self.parse_and()
                # default args capture current left/right, avoiding late-binding bug
                left = (lambda row, l=left, r=right: l(row) or r(row))
            return left

        def parse_and(self):
            left = self.parse_cmp()
            while self.peek()[0] == 'AND':
                self.advance()
                right = self.parse_cmp()
                left = (lambda row, l=left, r=right: l(row) and r(row))
            return left

        def parse_cmp(self):
            col_tok = self.expect('COL')
            col = col_tok[1]
            tok = self.peek()
            if tok[0] == 'LIKE':
                self.advance()
                pat_tok = self.expect('STR')
                return _make_like(col, pat_tok[1])
            if tok[0] == 'OP':
                self.advance()
                op = tok[1]
                val_tok = self.advance()
                if val_tok[0] not in ('NUM', 'STR', 'BOOL', 'NULL'):
                    raise ValueError(f"Expected value, got {val_tok[0]}")
                return _make_cmp(col, op, val_tok[1])
            raise ValueError(f"Expected OP or LIKE, got {tok[0]}")

    p = Parser(tokens)
    pred = p.parse()
    return [row for row in rows if pred(row)]

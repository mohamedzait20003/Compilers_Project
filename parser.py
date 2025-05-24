import sys

class SyntaxTreeNode:
    def __init__(self, label):
        self.label = label
        self.children = []

    def add(self, *nodes):
        self.children.extend(nodes)

class TokenStream:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def advance(self):
        self.position += 1

    def match(self, expected_type):
        token = self.current()
        if token and token[1] == expected_type:
            self.advance()
            return token
        self.error(f"Expected {expected_type}, got {token[1] if token else 'EOF'}")

    def error(self, message):
        token = self.current()
        token_info = f"at token {self.position + 1}: {token}" if token else "at end of input"
        raise SyntaxError(f"Syntax error {token_info} -> {message}")

def parse_program(ts):
    node = SyntaxTreeNode("program")
    node.add(parse_stmt_sequence(ts))
    return node

def parse_stmt_sequence(ts):
    node = SyntaxTreeNode("stmt_seq")
    node.add(parse_statement(ts))
    while ts.current() and ts.current()[1] == "SEMICOLON":
        ts.match("SEMICOLON")
        node.add(parse_statement(ts))
    return node

def parse_statement(ts):
    token = ts.current()
    if not token:
        ts.error("Unexpected end of input in statement")
    if token[1] == "IF":
        return parse_if_stmt(ts)
    elif token[1] == "REPEAT":
        return parse_repeat_stmt(ts)
    elif token[1] == "IDENTIFIER":
        return parse_assign_stmt(ts)
    elif token[1] == "READ":
        return parse_read_stmt(ts)
    elif token[1] == "WRITE":
        return parse_write_stmt(ts)
    else:
        ts.error(f"Unexpected token in statement: {token}")

def parse_if_stmt(ts):
    ts.match("IF")
    cond = parse_exp(ts)
    ts.match("THEN")
    then_branch = parse_stmt_sequence(ts)
    else_branch = None
    if ts.current() and ts.current()[1] == "ELSE":
        ts.match("ELSE")
        else_branch = parse_stmt_sequence(ts)
    ts.match("END")

    node = SyntaxTreeNode("if")
    node.add(cond, then_branch)
    if else_branch:
        node.add(else_branch)
    return node

def parse_repeat_stmt(ts):
    ts.match("REPEAT")
    body = parse_stmt_sequence(ts)
    ts.match("UNTIL")
    cond = parse_exp(ts)
    node = SyntaxTreeNode("repeat")
    node.add(body, cond)
    return node

def parse_assign_stmt(ts):
    var = ts.match("IDENTIFIER")[0]
    ts.match("ASSIGN")
    expr = parse_exp(ts)
    node = SyntaxTreeNode(f"assign ({var})")
    node.add(expr)
    return node

def parse_read_stmt(ts):
    var = ts.match("READ")
    id_token = ts.match("IDENTIFIER")[0]
    return SyntaxTreeNode(f"read ({id_token})")

def parse_write_stmt(ts):
    ts.match("WRITE")
    expr = parse_exp(ts)
    node = SyntaxTreeNode("write")
    node.add(expr)
    return node

def parse_exp(ts):
    left = parse_simple_exp(ts)
    if ts.current() and ts.current()[1] in ("LESSTHAN", "EQUAL"):
        op = ts.match(ts.current()[1])[0]
        right = parse_simple_exp(ts)
        node = SyntaxTreeNode(f"OP ({op})")
        node.add(left, right)
        return node
    return left

def parse_simple_exp(ts):
    left = parse_term(ts)
    while ts.current() and ts.current()[1] in ("PLUS", "MINUS"):
        op = ts.match(ts.current()[1])[0]
        right = parse_term(ts)
        new_node = SyntaxTreeNode(f"OP ({op})")
        new_node.add(left, right)
        left = new_node
    return left

def parse_term(ts):
    left = parse_factor(ts)
    while ts.current() and ts.current()[1] in ("MULT", "DIV"):
        op = ts.match(ts.current()[1])[0]
        right = parse_factor(ts)
        new_node = SyntaxTreeNode(f"OP ({op})")
        new_node.add(left, right)
        left = new_node
    return left

def parse_factor(ts):
    token = ts.current()
    if token[1] == "OPENBRACKET":
        ts.match("OPENBRACKET")
        expr = parse_exp(ts)
        ts.match("CLOSEDBRACKET")
        return expr
    elif token[1] == "NUMBER":
        value = ts.match("NUMBER")[0]
        return SyntaxTreeNode(f"const ({value})")
    elif token[1] == "IDENTIFIER":
        value = ts.match("IDENTIFIER")[0]
        return SyntaxTreeNode(f"id ({value})")
    else:
        ts.error("Expected NUMBER, IDENTIFIER, or (exp)")

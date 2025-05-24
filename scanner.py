import re

KEYWORDS = {
    'read': 'READ', 'write': 'WRITE',
    'if': 'IF', 'then': 'THEN', 'else': 'ELSE', 'end': 'END',
    'repeat': 'REPEAT', 'until': 'UNTIL'
}

SYMBOLS = {
    ';': 'SEMICOLON', ':=': 'ASSIGN',
    '+': 'PLUS', '-': 'MINUS', '*': 'MULT', '/': 'DIV',
    '=': 'EQUAL', '<': 'LESSTHAN',
    '(': 'OPENBRACKET', ')': 'CLOSEDBRACKET'
}

token_specification = [
    ('NUMBER',   r'\d+'),
    ('ASSIGN',   r':='),
    ('SYMBOL',   r'[;+\-*/=<>()]'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),    
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[\s\u00A0]+'), 
    ('MISMATCH', r'.')
]

def tokenize(code):
    tokens = []
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'NUMBER':
            tokens.append((value, 'NUMBER'))
        elif kind == 'ID':
            token_type = KEYWORDS.get(value, 'IDENTIFIER')
            tokens.append((value, token_type))
        elif kind == 'ASSIGN':
            tokens.append((value, SYMBOLS[':=']))
        elif kind == 'SYMBOL':
            token_type = SYMBOLS.get(value)
            if token_type:
                tokens.append((value, token_type))
        elif kind in ('SKIP', 'NEWLINE'):
            continue        
        elif kind == 'MISMATCH':
            char_code = f"(ASCII: {ord(value)})" if len(value) == 1 else ""
            raise RuntimeError(f'Unexpected character: "{value}" {char_code}')
    return tokens

def main():
    try:
        with open("sample_code.txt", "r") as file:
            code = file.read()
        tokens = tokenize(code)
        with open("tokens.txt", "w") as out:
            for value, token_type in tokens:
                out.write(f"{value},{token_type}\n")
        print("Scanning complete. Tokens written to tokens.txt.")
    except FileNotFoundError:
        print("Error: sample_code.txt not found.")
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    main()

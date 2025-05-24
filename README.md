# TINY Language Editor & Compiler

This project is a simple Integrated Development Environment (IDE) for the TINY language. It includes a code editor with syntax highlighting, a scanner (lexer), a parser, and a parse tree visualizer.

## Project Structure

-   `main.py`: The main application file that sets up the Tkinter GUI and integrates all components.
-   `scanner.py`: Contains the lexical analyzer (tokenizer) for the TINY language. It converts a stream of characters into a stream of tokens.
-   `parser.py`: Implements the parser for the TINY language. It takes tokens from the scanner and builds a syntax tree.
-   `visualizer.py`: Uses Graphviz to generate a visual representation of the parse tree.

## Features

-   **Code Editor**:
    -   A text area for writing and editing TINY language code.
    -   Basic editor functions like Cut, Copy, Paste (via context menu).
    -   Toggleable Light/Dark themes for the editor interface.
-   **Scanner (Lexer)**:
    -   Identifies keywords, identifiers, numbers, and symbols based on predefined rules.
    -   Handles whitespace and comments.
    -   Outputs a list of tokens with their types and values.
-   **Parser**:
    -   Implements a recursive descent parser for the TINY language grammar.
    -   Constructs a `SyntaxTreeNode` based Abstract Syntax Tree (AST) representing the code\'s structure.
    -   Provides error handling for syntax errors.
-   **Parse Tree Visualization**:
    -   Generates a graphical representation of the AST using the `graphviz` library.
    -   Allows users to view the generated parse tree within the application.
    -   Supports exporting the parse tree as PNG or PDF.
-   **Output Area**:
    -   Displays messages from the scanner and parser, including token lists and error messages.

## TINY Language Grammar (Inferred)

The parser seems to support a grammar similar to this (based on the parsing functions):

```
program -> stmt_sequence

stmt_sequence -> statement { ; statement }

statement -> if_stmt | repeat_stmt | assign_stmt | read_stmt | write_stmt

if_stmt -> \'if\' exp \'then\' stmt_sequence [ \'else\' stmt_sequence ] \'end\'

repeat_stmt -> \'repeat\' stmt_sequence \'until\' exp

assign_stmt -> IDENTIFIER \':=\' exp

read_stmt -> \'read\' IDENTIFIER

write_stmt -> \'write\' exp

exp -> simple_exp [ comparison_op simple_exp ]

simple_exp -> term { add_op term }

term -> factor { mul_op factor }

factor -> \'(\' exp \')\' | NUMBER | IDENTIFIER

comparison_op -> \'<\' | \'=\'
add_op -> \'+\' | \'-\'
mul_op -> \'*\' | \'/\'
```

## How to Run

1.  **Prerequisites**:
    *   Python 3.x
    *   Tkinter (usually included with Python)
    *   Pillow (PIL Fork): `pip install Pillow`
    *   Graphviz library: `pip install graphviz`
    *   Graphviz software: Must be installed separately and added to your system's PATH. (Download from [graphviz.org](https://graphviz.org/download/))

2.  **Running the Application**:
    ```bash
    python main.py
    ```

3.  **Using the Editor**:
    *   Type or paste your TINY language code into the editor pane.
    *   Click "Parse" to tokenize and parse the code.
    *   The output area will show the tokens and any errors.
    *   If parsing is successful, the view will switch to the parse tree visualizer.
    *   In the tree view, you can "Return to Editor" or "Export Tree" (as PNG or PDF).
    *   Use "View" > "Toggle Light/Dark Mode" to change the theme.
    *   "Erase" button clears the code editor.

## Using the Pre-built Executable

The pre-built executable, `main.exe`, is located in the `dist` folder.

To run the application using this executable:

1.  **Ensure Graphviz is Installed and in PATH**:
    *   The `main.exe` requires Graphviz to be installed on your system for the parse tree visualization feature to work.
    *   Download and install Graphviz from [graphviz.org](https://graphviz.org/download/).
    *   **Crucially, ensure that the `bin` directory of your Graphviz installation (e.g., `C:\\Program Files\\Graphviz\\bin`) is added to your system's PATH environment variable.**

2.  **Run the Executable**:
    *   Navigate to the `dist` folder.
    *   Double-click `main.exe` or run it from the command line.

## Key Components and Logic

### `main.py` - `CodeEditorApp` Class

*   **Initialization (`__init__`)**: Sets up the main window, themes, frames for editor and tree view, menus, and widgets.
*   **View Switching (`show_editor_view`, `show_tree_view`)**: Manages visibility of the editor and tree view frames.
*   **Tree Display (`_resize_and_display_tree_image`, `_on_canvas_configure`)**: Handles rendering and resizing the parse tree image on a Tkinter canvas.
*   **Theming (`apply_theme`, `toggle_theme`)**: Applies light or dark mode styles to UI elements.
*   **Code Parsing (`parse_code`)**:
    *   Gets code from the editor.
    *   Calls `scanner.tokenize()` to get tokens.
    *   Creates a `parser.TokenStream`.
    *   Calls `parser.parse_program()` to get the AST root.
    *   Uses `visualizer.TreeVisualizer` to render the tree.
    *   Displays the tree or error messages.
*   **Exporting (`export_tree_as_png`, `export_tree_as_pdf`)**: Saves the current `Digraph` object (parse tree) to a file.

### `scanner.py`

*   **`KEYWORDS`, `SYMBOLS`**: Dictionaries mapping lexemes to token types.
*   **`token_specification`**: A list of regex patterns for token recognition.
*   **`tokenize(code)`**:
    *   Uses `re.finditer` with a combined regex to find all matches.
    *   Categorizes matches into `NUMBER`, `ID` (checking for keywords), `ASSIGN`, `SYMBOL`, or `MISMATCH`.
    *   Skips whitespace and newlines.
    *   Returns a list of `(value, type)` tuples.

### `parser.py`

*   **`SyntaxTreeNode`**: A simple class to represent nodes in the AST, with a label and children.
*   **`TokenStream`**: A helper class to manage the list of tokens, providing methods to `current()`, `advance()`, and `match()` expected tokens.
*   **Parsing Functions (`parse_program`, `parse_stmt_sequence`, `parse_statement`, etc.)**:
    *   These functions implement a recursive descent parser. Each function corresponds to a non-terminal in the TINY language grammar.
    *   They consume tokens from the `TokenStream` and build `SyntaxTreeNode` objects.
    *   `error()` method in `TokenStream` is used for syntax error reporting.

### `visualizer.py` - `TreeVisualizer` Class

*   **`__init__`**: Initializes Graphviz settings.
*   **`_add_nodes_edges(dot, node, parent_id)`**: Recursively traverses the `SyntaxTreeNode` structure.
    *   Creates a unique ID for each node.
    *   Adds nodes to the `Digraph` object with specific shapes and colors based on the node\'s label (e.g., keywords, operators, identifiers).\
    *   Adds edges connecting parent nodes to child nodes.
*   **`render_tree(root)`**:
    *   Takes the root of the `SyntaxTreeNode` AST.
    *   Creates a new `Digraph` object.
    *   Calls `_add_nodes_edges` to populate the graph.
    *   Returns the `Digraph` object, which can then be rendered to various formats (PNG, PDF, etc.) by `main.py`.

This README provides a comprehensive overview of the TINY Language Editor project.

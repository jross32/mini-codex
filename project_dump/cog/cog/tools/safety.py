"""Code safety checks for AI-generated changes."""
import os
import ast
import pyflakes.api
import pyflakes.reporter
import pyflakes.messages
import tempfile

class QuietReporter:
    """Capture pyflakes errors without printing."""
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def unexpectedError(self, filename, msg):
        self.errors.append(str(msg))
    
    def syntaxError(self, filename, msg, lineno, offset, text):
        self.errors.append(f"Line {lineno}: {msg}")
    
    def flake(self, msg):
        text = f"Line {msg.lineno}: {msg.message % msg.message_args}"
        if isinstance(msg, pyflakes.messages.UndefinedName):
            self.errors.append(text)
        elif isinstance(msg, (pyflakes.messages.UnusedImport,
                            pyflakes.messages.UnusedVariable,
                            pyflakes.messages.RedefinedWhileUnused)):
            self.warnings.append(text)
        else:
            self.errors.append(text)

def check_python_syntax(code: str, filename: str) -> tuple[bool, list[str]]:
    """Check Python code for syntax and basic logic errors.
    Returns (is_valid, list_of_errors)."""
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, [f"Line {e.lineno}: {e.msg}"]
    
    reporter = QuietReporter()
    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        tmp_path = tmp.name
        tmp.write(code)
        tmp.close()  # Close before pyflakes reads it
        
        pyflakes.api.checkPath(tmp_path, reporter)
    except Exception as e:
        return False, [str(e)]
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass  # Ignore cleanup errors
    
    # Report errors for syntax errors and undefined names
    return not bool(reporter.errors), reporter.errors

def check_template_syntax(code: str, filename: str) -> tuple[bool, list[str]]:
    """Basic check for HTML/template syntax.
    Returns (is_valid, list_of_errors)."""
    try:
        from jinja2 import Environment
        env = Environment()
        env.parse(code)
    except Exception as e:
        return False, [f"Template syntax error: {str(e)}"]
    
    # Check for unescaped variables that could enable XSS
    if "{{" in code and not "|escape" in code and not "|e" in code and not "|safe" in code:
        return False, ["Warning: Template contains variables without explicit escaping"]
    
    return True, []

def check_file_safety(filename: str, content: str) -> tuple[bool, list[str]]:
    """Check if file content is safe to apply.
    Returns (is_safe, list_of_errors)."""
    # First check for dangerous characters in all files
    
    # Check for surrogates, BOM, and other invalid Unicode
    for i, c in enumerate(content):
        # Check for surrogate characters (0xD800-0xDFFF range)
        if 0xD800 <= ord(c) <= 0xDFFF:
            return False, ["File contains invalid Unicode characters (surrogate detected)"]
        
        # Check for BOM at start
        if i == 0 and ord(c) in (0xFEFF, 0xFFFE):
            return False, ["File contains invalid Unicode characters (BOM detected)"]
        
        try:
            # Try encoding to UTF-8 to validate character
            c.encode('utf-8')
        except UnicodeEncodeError:
            return False, ["File contains invalid Unicode characters"]
    
    # Check for null bytes and control chars
    if '\0' in content or any(ord(c) < 32 and c not in '\n\r\t' for c in content):
        return False, ["File contains invalid Unicode characters"]
    
    # Then do specific checks by file type
    if filename.endswith('.py'):
        return check_python_syntax(content, filename)
    elif filename.endswith('.html'):
        return check_template_syntax(content, filename)
    else:
        return True, []
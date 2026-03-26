"""Test code safety checks."""
import pytest
from tools.safety import check_python_syntax, check_template_syntax, check_file_safety

def test_python_syntax_check():
    """Test Python syntax validation."""
    # Valid code
    code = "def hello():\n    print('Hello world')\n    return 42"
    is_valid, errors = check_python_syntax(code, "test.py")
    assert is_valid
    assert not errors    # Invalid syntax
    code = """def broken()
    print("missing colon"
"""
    is_valid, errors = check_python_syntax(code, "test.py")
    assert not is_valid
    assert len(errors) > 0
    
    # Undefined name warning
    code = """def use_undefined():
    print(undefined_var)
"""
    is_valid, errors = check_python_syntax(code, "test.py")
    assert not is_valid
    assert any("undefined_var" in e for e in errors)

def test_template_syntax_check():
    """Test template syntax validation."""
    # Valid template
    template = """{% extends "base.html" %}
{% block content %}
<h1>{{ title|escape }}</h1>
<p>{{ text|e }}</p>
{% endblock %}
"""
    is_valid, errors = check_template_syntax(template, "test.html")
    assert is_valid
    assert not errors
    
    # Invalid syntax
    template = """{% extends "base.html" %}
{% block content %}
{{ unclosed_var
{% endblock %}
"""
    is_valid, errors = check_template_syntax(template, "test.html")
    assert not is_valid
    assert len(errors) > 0
    
    # Missing escaping warning
    template = """<div>{{ user_input }}</div>"""
    is_valid, errors = check_template_syntax(template, "test.html")
    assert not is_valid  # fails because of potential XSS
    assert any("escaping" in e for e in errors)

def test_file_safety_check():
    """Test overall file safety checking."""
    # Python file with proper imports
    code = "import os\nprint('Hello')"
    is_safe, errors = check_file_safety("test.py", code)
    assert is_safe
    assert not errors
    
    # Template file
    is_safe, errors = check_file_safety("test.html", "<p>{{ text|e }}</p>")
    assert is_safe
    assert not errors
    
    # Invalid Unicode using surrogate escapes
    is_safe, errors = check_file_safety("test.txt", '\udcff\udcfe')  # Encoded form of b'\xff\xfe'
    assert not is_safe
    assert any("Unicode" in e for e in errors)
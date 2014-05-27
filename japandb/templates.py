# templates.py
# module responsible for which templates are which,
# as well as which

import json
from flask import render_template

def inject_python_builtins():
    import builtins
    return builtins.__dict__

def setup(app):
    app.context_processor(inject_python_builtins)

# ehhh...
def render(name, **kwargs):
    return render_template(name + '.html', **kwargs)

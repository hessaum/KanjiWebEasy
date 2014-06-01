# templates.py
# module responsible for which templates are which,
# as well as which

import json
from flask import render_template

def inject_python_builtins():
    import builtins
    return builtins.__dict__

def inject_constants():
    return dict(
        SITE_TITLE='ArataTori'
    )

def setup(app):
    app.context_processor(inject_python_builtins)
    app.context_processor(inject_constants)

# ehhh...
def render(name, **kwargs):
    return render_template(name + '.html', **kwargs)

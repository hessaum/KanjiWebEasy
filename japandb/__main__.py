from __future__ import absolute_import
from japandb.appmain import app
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.run(debug=True, host='0.0.0.0')

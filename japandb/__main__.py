from __future__ import absolute_import
from japandb.appmain import app
app.run(debug=False, host='0.0.0.0')

app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))
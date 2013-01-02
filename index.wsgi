import sae
from littesnail import wsgi

application = sae.create_wsgi_app(wsgi.application)
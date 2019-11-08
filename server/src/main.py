import os

import jinja2
import webapp2

from modules.base.handlers import BaseHandler, get_webapp2_config, routes as base_routes
from modules.links.handlers import routes as link_routes
from modules.routing.handlers import routes as routing_routes
from modules.users.handlers import routes as user_routes
from shared_helpers.env import current_env_is_local

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'static')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(BaseHandler):

    def check_authorization(self):
        pass

    def get(self):
        if not self.user:
          self.redirect('https://www.trot.to'
                        if self.request.host == 'trot.to'
                        else '/_/auth/login')

        template = JINJA_ENVIRONMENT.get_template('index.html')

        self.response.write(template.render(
            {'alreadyAcceptedTerms': self.session.get('already_accepted_terms', False),
             'csrf_token': self.session.get('csrf_token', '')}
        ))

app = webapp2.WSGIApplication(
    [('/', MainHandler)],
    config=get_webapp2_config(),
    debug=False
)


def main():
  routes = [('/', MainHandler)]
  routes = routes + base_routes + link_routes + user_routes + routing_routes

  app = webapp2.WSGIApplication(routes,
                                config=get_webapp2_config(),
                                debug=current_env_is_local())

  from paste import httpserver
  httpserver.serve(app, host='0.0.0.0', port='9095')


if __name__ == '__main__':
  main()

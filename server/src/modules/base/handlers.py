import base64
import datetime
import json
import logging
import os
import httplib2
import pickle

import jinja2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import webapp2
from webapp2_extras import sessions

from modules.base import authentication
from modules.organizations.utils import get_organization_id_for_email
from modules.users.helpers import get_or_create_user
from shared_helpers.configs import get_secrets, get_path_to_oauth_secrets
from shared_helpers import env
from shared_helpers import utils


JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../../static/templates')),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True)


class BaseHandler(webapp2.RequestHandler):

  def options(self, **kwargs):
    return

  def render_login_selector_page(self, oauth_redirect_uri=None, redirect_to_after_oauth=None):
    template = JINJA_ENVIRONMENT.get_template('auth/login_selector.html')

    google_auth_url = self.get_google_login_url(oauth_redirect_uri, redirect_to_after_oauth)

    self.response.write(template.render({'google_auth_url': google_auth_url}))

  def check_authorization(self):
    self.abort(403)  # conservative default

  def attempt_auth_by_user_header(self):
    # only for testing
    if not env.current_env_is_local():
      return

    if self.request.headers.get('TROTTO_USER_UNDER_TEST'):
      self.user_email = self.request.headers.get('TROTTO_USER_UNDER_TEST')
      self.user_org = get_organization_id_for_email(self.user_email)

  def get_google_login_url(self, oauth_redirect_uri=None, redirect_to_after_oauth=None):
    if not oauth_redirect_uri:
      oauth_redirect_uri = '%s%s' % (
        'http://localhost:9095' if self.request.host.startswith('localhost')
        else self.request.host_url.replace('http://', 'https://'),
        '/_/auth/oauth2_callback')

    if not redirect_to_after_oauth:
      redirect_to_after_oauth = 'http://localhost:5007' if self.request.host.startswith('localhost') else '/'

    self.session['redirect_to_after_oauth'] = str(redirect_to_after_oauth)

    # http://oauth2client.readthedocs.io/en/latest/source/oauth2client.client.html
    flow = flow_from_clientsecrets(get_path_to_oauth_secrets(),
                                   scope='https://www.googleapis.com/auth/userinfo.email',
                                   redirect_uri=oauth_redirect_uri)

    self.session['pickled_oauth_flow'] = pickle.dumps(flow)
    self.session['oauth_state'] = utils.generate_secret(32)
    try:
      return str(flow.step1_get_authorize_url(state=self.session['oauth_state']))
    except TypeError:
      # TODO: Fix breakage only appearing in tests.
      return str(flow.step1_get_authorize_url())

  def force_to_original_url(self):
    self.redirect(str('%s://%s?tr=ot' % (self.request.get('sc'), self.request.path[1:])))

  def dispatch(self):
    if self.request.host == 'dev.trot.to':
      # TODO: Properly dismantle code specific to dev.trot.to.
      self.abort(403)

    self.is_local_env = env.current_env_is_local()

    # Get a session store for this request.
    self.session_store = sessions.get_store(request=self.request)

    self.login_error = None

    self.user_email = None
    self.user = None

    if not self.user_email:
      self.user_email = self.session.get('user_email')
      self.user_org = get_organization_id_for_email(self.user_email) if self.user_email else None

    if not self.user_email and env.current_env_is_local():
      self.attempt_auth_by_user_header()

    self.session['already_accepted_terms'] = False
    if self.user_email:
      self.user = get_or_create_user(self.user_email, self.user_org)
      self.session['already_accepted_terms'] = not not self.user.accepted_terms_at

      if not self.session.get('csrf_token'):
        self.session['csrf_token'] = utils.generate_secret(32)

    try:
      self.redirect_to = None
      self.check_authorization()

      if self.redirect_to:
        self.response.write(json.dumps({'redirect_to': self.redirect_to}))
        return

      # Dispatch the request.
      webapp2.RequestHandler.dispatch(self)
    finally:
      # Save all sessions, IFF secure connection
      if self.request.scheme == 'https' or self.is_local_env:
        self.session_store.save_sessions(self.response)

  @webapp2.cached_property
  def session(self):
    # Returns a session using the default cookie key.
    # see https://webapp2.readthedocs.io/en/latest/api/webapp2_extras/sessions.html#webapp2_extras.sessions.SessionStore

    if env.get_platform() == env.APP_ENGINE_PLATFORM_ID:
      backend = 'datastore'  # uses App Engine db
    else:
      # TODO: Move away from using securecookie and always use a backend. For the moment, non-GAE deployments are
      #       self-hosted, so some OAuth credentials appearing in the secure cookie isn't so concerning, but that's
      #       not acceptable if the main Trotto instance is migrated to a different database.
      backend = 'securecookie'

    return self.session_store.get_session(max_age=2592000,  # one month
                                          backend=backend)


class NoLoginRequiredHandler(BaseHandler):

  def check_authorization(self):
    pass


class UserRequiredHandler(BaseHandler):

  def check_authorization(self):
    if not self.user_email:
      request_data = {
        'origin': self.request.headers.get('Origin'),
        'method': self.request.method,
        'path': self.request.path,
        'body': self.request.body
      }

      if 'slack' in self.request.path_url:
        self.abort(400)  # Guard against leaking Slack token or other sensitive data in response

      self.redirect_to = '%s/play_queued_request?r=%s' % (self.request.path_url.rstrip('/'),
                                                          base64.urlsafe_b64encode(json.dumps(request_data)))

    if (not env.current_env_is_local()
        and self.request.method not in ['GET', 'OPTIONS']
        and self.request.headers.get('X-CSRF') != self.session.get('csrf_token')):
      self.abort(401)


class OAuthCallbackHandler(NoLoginRequiredHandler):

  def get(self):
    if self.session.get('pickled_oauth_flow'):
      flow = pickle.loads(self.session['pickled_oauth_flow'])
    else:
      flow = flow_from_clientsecrets(get_path_to_oauth_secrets(),
                                     scope='https://www.googleapis.com/auth/userinfo.email',
                                     redirect_uri='https://trot.to/_/auth/oauth2_callback')

    if not self.session.get('oauth_state') or self.session.get('oauth_state') != self.request.get('state'):
      self.redirect('/_/auth/login')
      return

    try:
      credentials = flow.step2_exchange(self.request.get('code'))
    except (FlowExchangeError, ValueError):
      # user declined to auth; move on
      self.redirect(self.session.get('redirect_to_after_oauth', '/'))
      return

    self.session['credentials'] = pickle.dumps(credentials)

    self.session['user_email'] = authentication.get_user_email(credentials)

    del self.session['credentials']

    user = get_or_create_user(self.session['user_email'], get_organization_id_for_email(self.session['user_email']))
    if not user.accepted_terms_at:
      # all login methods now have UI for consenting to terms
      user.accepted_terms_at = datetime.datetime.utcnow()
      user.put()

      # quick & dirty workaround for issue where user login gets overwritten by
      # conflicting request

    self.response.write("""<!doctype html>
<html>
  <head>
    <title>Redirecting...</title>
    <script>window.location.href="%s"</script>
  </head>
  <body></body>
</html>""" % (self.session.get('redirect_to_after_oauth', '/')))


class LogoutHandler(NoLoginRequiredHandler):

  def get(self):
    """Both clears session data (user email, etc.) and revokes Google OAuth so a different user can be selected."""

    try:
      credentials = pickle.loads(self.session['credentials'])
      http = httplib2.Http()
      http = credentials.authorize(http)
      credentials.revoke(http)
    except:
      pass

    self.session.clear()  # remove session data

    self.redirect('http://localhost:5007/' if self.request.host.startswith('localhost') else '/')


class LoginHandler(NoLoginRequiredHandler):

  def get(self):
    redirect_to = self.request.get('redirect_to', None)

    # quick & dirty workaround for issue were session isn't set before redirect.
    self.response.write("""<!doctype html>
<html>
  <head>
    <title>Redirecting...</title>
    <script>window.location.href="%s"</script>
  </head>
  <body></body>
</html>""" % (self.get_google_login_url(None, redirect_to)))


class GoogleLoginHandler(NoLoginRequiredHandler):

  def get(self):
    self.redirect(self.get_google_login_url())


def get_webapp2_config():
  try:
    sessions_secret = get_secrets()['sessions_secret']
  except IOError:
    if env.current_env_is_local():
      sessions_secret = 'local-only-mock-sessions-secret'
    else:
      raise

  config = {}
  config['webapp2_extras.sessions'] = {
    'secret_key': sessions_secret,
    'cookie_args': {
      'secure': env.current_env_is_production()
    }
  }

  return config


routes = [
  ('/_/auth/oauth2_callback', OAuthCallbackHandler),
  ('/_/auth/logout', LogoutHandler),
  ('/_/auth/login', LoginHandler),
  ('/_/auth/login/google', GoogleLoginHandler)
]


app = webapp2.WSGIApplication(routes,
                              config=get_webapp2_config(),
                              debug=False)

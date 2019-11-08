import httplib2

from apiclient.discovery import build


def get_user_email(oauth_credentials):
  user_info_service = build(
    serviceName='oauth2', version='v2',
    http=oauth_credentials.authorize(httplib2.Http()))

  user_info = user_info_service.userinfo().get().execute()

  if not user_info['verified_email']:
    return None

  return user_info['email'].lower()

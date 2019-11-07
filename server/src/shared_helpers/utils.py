import base64
import datetime
import os


def generate_secret(number_of_bytes):
  return base64.urlsafe_b64encode(os.urandom(number_of_bytes)).strip('=')


DATETIME_FORMAT = '%Y%m%d%H%M%S'

def datetime_to_string(dt):
  return dt.strftime(DATETIME_FORMAT)

def string_to_datetime(a_string):
  return datetime.datetime.strptime(a_string, DATETIME_FORMAT)

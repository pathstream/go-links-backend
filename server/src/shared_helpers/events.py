"""Helper for delivering events to subscribing URLs. At the moment, this only works when running Trotto on GAE."""

import json
import time
import uuid

from shared_helpers.env import get_platform, APP_ENGINE_PLATFORM_ID

if get_platform() == APP_ENGINE_PLATFORM_ID:
 from google.appengine.ext.deferred import defer
else:
  def defer(*args, **kwargs):
    pass

import requests

import configs


def _deliver_event_to_url(url, event_object):
  # TODO: Sign requests.
  requests.post(url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(event_object))


def _deliver_event(event_id, event_type, timestamp, object_type, object_data):
  object_data['object'] = object_type

  event_object = {'id': event_id,
                  'type': event_type,
                  'created': timestamp,
                  'data': {'object': object_data}}

  for url in configs.get_config().get('event_subscribers', []):
    defer(_deliver_event_to_url,
          url,
          event_object,
          _queue='events')


def enqueue_event(event_type, object_type, object_data, timestamp=None):
  event_timestamp = timestamp or time.time()
  event_id = uuid.uuid4().hex

  defer(_deliver_event,
        event_id,
        event_type,
        event_timestamp,
        object_type,
        object_data,
        _queue='events')

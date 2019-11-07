from google.appengine.ext import ndb

from modules.data.implementations.cloud_datastore.base import BaseModel
from modules.organizations.utils import get_organization_id_for_email


class User(BaseModel):
  email = ndb.StringProperty(required=True)
  organization = ndb.StringProperty()
  role = ndb.StringProperty(choices=['implementer'])
  accepted_terms_at = ndb.DateTimeProperty()
  domain_type = ndb.StringProperty(choices=['generic', 'corporate'])
  notifications = ndb.JsonProperty(default={})

  def extract_organization(self):
    return get_organization_id_for_email(self.email) if self.email else None

  def get_organization_name(self):
    return get_organization_id_for_email(self.email) if self.email else None

  @staticmethod
  def get_by_email(email):
    User.query(User.email == email).get()

from datetime import datetime

from modules.data.abstract.base import BaseModel
from modules.organizations.utils import get_organization_id_for_email


class User(BaseModel):
  email = unicode
  organization = unicode
  role = unicode
  accepted_terms_at = datetime
  domain_type = unicode
  notifications = dict

  # TODO: Eliminate the need for this duplication with a better base class.
  _properties = ['id', 'oid', 'created', 'modified',
                 'email', 'organization', 'role', 'accepted_terms_at',
                 'domain_type', 'notifications']

  def extract_organization(self):
    return get_organization_id_for_email(self.email) if self.email else None

  def get_organization_name(self):
    return get_organization_id_for_email(self.email) if self.email else None

  @staticmethod
  def get_by_email(email):
    raise NotImplementedError

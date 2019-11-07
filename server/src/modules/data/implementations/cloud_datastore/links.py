from google.appengine.ext import ndb

from modules.data.implementations.cloud_datastore.base import BaseModel


class ShortLink(BaseModel):
  organization = ndb.StringProperty(required=True)
  owner = ndb.StringProperty(required=True)
  shortpath = ndb.StringProperty(required=True)
  # TODO: Make shortpath_prefix a computed property.
  shortpath_prefix = ndb.StringProperty()  # first part of path; for doing quick search for templates
  destination_url = ndb.StringProperty(required=True)
  visits_count = ndb.IntegerProperty()
  visits_count_last_updated = ndb.DateTimeProperty()

  @staticmethod
  def get_by_prefix(organization, shortpath_prefix):
    return ShortLink.query(
      ShortLink.organization == organization,
      ShortLink.shortpath_prefix == shortpath_prefix
    ).fetch(limit=None)

  @staticmethod
  def get_by_full_path(organization, shortpath):
    return ShortLink.query(
      ShortLink.organization == organization,
      ShortLink.shortpath == shortpath
    ).get()

  # TODO: Handle more links (paginate).
  @staticmethod
  def get_by_organization(organization):
    return ShortLink.query(
      ShortLink.organization == organization
    ).fetch(limit=10000)

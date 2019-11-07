import sqlite3
import time

from modules.data.abstract import links
from shared_helpers import utils

conn = sqlite3.connect('trotto.db')

try:
  conn.execute('''CREATE TABLE links
    (id integer, organization text, owner text, shortpath text, shortpath_prefix text, destination_url text, visits_count integer, visits_count_last_updated text)''')
except sqlite3.OperationalError:
  pass


def _row_to_object(link):
  return ShortLink(id=link[0],
                   organization=link[1],
                   owner=link[2],
                   shortpath=link[3],
                   shortpath_prefix=link[4],
                   destination_url=link[5],
                   visits_count=int(link[6] or 0),
                   visits_count_last_updated=utils.string_to_datetime(link[6]) if link[7] else None)


class ShortLink(links.ShortLink):
  @staticmethod
  def get_by_id(id):
    conn = sqlite3.connect('trotto.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM links WHERE id=?', (id,))

    link = cursor.fetchone()

    conn.close()

    if not link:
      return None

    return _row_to_object(link)

  @staticmethod
  def get_by_prefix(organization, shortpath_prefix):
    raise NotImplementedError

  @staticmethod
  def get_by_full_path(organization, shortpath):
    conn = sqlite3.connect('trotto.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM links WHERE organization=? AND shortpath=?', (organization, shortpath))

    link = cursor.fetchone()

    conn.close()

    if not link:
      return None

    return _row_to_object(link)

  @staticmethod
  def get_by_organization(organization):
    conn = sqlite3.connect('trotto.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM links')
    links = [_row_to_object(link) for link in cursor]

    conn.close()

    return links

  def put(self):
    conn = sqlite3.connect('trotto.db')
    cursor = conn.cursor()

    visits_count_last_updated = (utils.datetime_to_string(self.visits_count_last_updated)
                                 if self.visits_count_last_updated
                                 else None)

    if self.id:
      cursor.execute('''UPDATE links
                        SET organization=?, owner=?, shortpath=?, shortpath_prefix=?,
                            destination_url=?, visits_count=?, visits_count_last_updated=?
                        WHERE id=?''',
                     (self.organization, self.owner, self.shortpath, self.shortpath_prefix,
                      self.destination_url, self.visits_count, visits_count_last_updated, self.id))
    else:
      new_id = int(time.time())

      cursor.execute('INSERT INTO links values (?, ?, ?, ?, ?, ?, ?, ?)',
                     (new_id, self.organization, self.owner, self.shortpath, self.shortpath_prefix,
                      self.destination_url, self.visits_count, visits_count_last_updated))

      self.id = new_id

    cursor.close()

    conn.commit()

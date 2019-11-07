import json
import sqlite3
import time

from modules.data.abstract import users
from shared_helpers import utils

conn = sqlite3.connect('trotto.db')

try:
  conn.execute('''CREATE TABLE users
    (id integer, email text, organization text, role text, accepted_terms_at text, domain_type text, notifications text)''')
except sqlite3.OperationalError:
  pass

class User(users.User):

  @staticmethod
  def get_by_email(email):
    conn = sqlite3.connect('trotto.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email=?', (email,))
    user = cursor.fetchone()

    cursor.close()

    if not user:
      return None

    return User(id=user[0],
                email=user[1],
                organization=user[2],
                role=user[3],
                accepted_terms_at=utils.string_to_datetime(user[4]) if user[3] else None,
                domain_type=user[5],
                notifications=json.loads(user[6]))

  def put(self):
    conn = sqlite3.connect('trotto.db')
    cursor = conn.cursor()

    accepted_terms_at = utils.datetime_to_string(self.accepted_terms_at) if self.accepted_terms_at else None

    if self.id:
      cursor.execute('''UPDATE users
                        SET email=?, organization=?, role=?, accepted_terms_at=?, domain_type=?, notifications=?
                        WHERE id=?''',
                     (self.email, self.organization, self.role, accepted_terms_at,
                      self.domain_type, json.dumps(self.notifications), self.id))
    else:
      new_id = int(time.time())

      cursor.execute('INSERT INTO users values (?, ?, ?, ?, ?, ?, ?)',
                     (new_id, self.email, self.organization, self.role, accepted_terms_at,
                      self.domain_type, json.dumps(self.notifications)))
      self.id = new_id

    cursor.close()

    conn.commit()

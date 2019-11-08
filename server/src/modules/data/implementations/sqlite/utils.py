import time

def get_pretty_unique_id():
  return int(round(time.time() * 1000))

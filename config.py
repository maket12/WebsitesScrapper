
PROXY_REFRESH_INTERVAL = 20  # seconds

class Config:
  def __init__(self, is_full_parse=False, reset_state=False):
    self.is_full_parse = is_full_parse
    self.reset_state = reset_state

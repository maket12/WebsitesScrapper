
ASOCKS_API_KEY = "GcxSc9HRv6pnLVurZIqSU0SacgaoIE3r"
PROXY_REFRESH_INTERVAL = 15 # seconds

class Config:
  def __init__(self, is_full_parse=False, reset_state=False):
    self.is_full_parse = is_full_parse
    self.reset_state = reset_state

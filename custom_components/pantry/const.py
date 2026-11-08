"""Constants for the Pantry integration."""
from datetime import timedelta

DOMAIN = "pantry"
CONF_URL = "url"
CONF_TOKEN = "token"
UPDATE_INTERVAL = timedelta(minutes=5)
PREP_EVENT_MINUTES = 15          # how long a prep task lasts on the calendar
MIN_PANTRY_VERSION = "2026.11.8"  # oldest Pantry (on the PC) this integration works with

"""Constants for the ProfitEMS integration."""

from datetime import timedelta

DOMAIN = "profitems"
API_URL = "https://panel.profitems.pl/api/v1/instalacja"
# The server refreshes installation data every 5 minutes; its limit is 60 requests per 15 minutes.
UPDATE_INTERVAL = timedelta(seconds=60)

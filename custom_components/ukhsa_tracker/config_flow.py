"""Config flow for UKHSA Respiratory Tracker."""
from homeassistant import config_entries
from . import DOMAIN

class UkhsaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
	"""Handle a config flow for UKHSA Tracker."""

	VERSION = 1

	async def async_step_user(self, user_input=None):
		"""Handle the initial step."""
		# Check if an entry already exists, as we only need one.
		if self._async_current_entries():
			return self.async_abort(reason="single_instance_allowed")

		# Create the configuration entry, which triggers the setup in __init__.py
		return self.async_create_entry(title="UKHSA Respiratory Tracker", data={})

	def _async_current_entries(self):
		"""Return the current entries."""
		return self.hass.config_entries.async_entries(DOMAIN)
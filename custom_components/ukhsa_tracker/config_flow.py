"""Config flow for UKHSA Respiratory Tracker."""
from homeassistant import config_entries
from . import DOMAIN

class UkhsaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
	"""Handle a config flow for UKHSA Tracker."""

	VERSION = 1

	async def async_step_user(self, user_input=None):
		"""Handle the initial step."""
		# This will create a single instance of the integration.
		if self._async_current_entries():
			return self.async_abort(reason="single_instance_allowed")

		return self.async_create_entry(title="UKHSA Respiratory Tracker", data={})

	def _async_current_entries(self):
		"""Return the current entries."""
		return self.hass.config_entries.async_entries(DOMAIN)
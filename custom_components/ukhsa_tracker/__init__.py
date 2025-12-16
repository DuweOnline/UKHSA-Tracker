# __init__.py

"""The UKHSA Respiratory Tracker integration."""
import logging
import requests
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ukhsa_tracker"
PLATFORMS = ["sensor"]

# The UKHSA API updates weekly, so we check daily.
UPDATE_INTERVAL = timedelta(hours=24) 

class UkhsaApi:
	"""Class to handle API fetching from UKHSA."""
	def __init__(self):
		"""Initialize the API client."""
		# Base URL structured for Nation (England) and variable topic/metric
		self.base_url = "https://api.ukhsa-dashboard.data.gov.uk/themes/infectious_disease/sub_themes/respiratory/topics/{topic}/geography_types/Nation/geographies/England/metrics/{metric}"

	def get_data(self, topic: str, metric: str):
		"""Fetch the latest data point for a given topic and metric."""
		url = self.base_url.format(topic=topic, metric=metric)
		_LOGGER.debug("Fetching data from: %s", url)

		try:
			# Add a timeout for robustness
			response = requests.get(url, timeout=30)
			response.raise_for_status()
			data = response.json()
		except requests.exceptions.RequestException as err:
			_LOGGER.error("Error fetching data from UKHSA: %s", err)
			raise UpdateFailed(f"Error fetching data: {err}") from err

		# The API returns an array of results; we want the first (latest) one.
		if data.get("results") and data["results"]:
			latest_result = data["results"][0]
			return {
				"value": latest_result.get("metric_value"),
				"date": latest_result.get("date"),
				"geography": latest_result.get("geography"),
			}
		
		_LOGGER.warning("No results found for topic: %s, metric: %s", topic, metric)
		return None

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
	"""Set up the Ukhsa Tracker from a config entry."""
	
	# Store the API client and coordinator in HA data
	if DOMAIN not in hass.data:
		hass.data[DOMAIN] = {}

	api = UkhsaApi()
	
	async def async_update_data():
		"""Fetch data from the API and store it, handling partial failures."""
		_LOGGER.info("Starting UKHSA data update")
		
		data = {}
		
		# 1. COVID-19 Data (Hospital Admissions Rate)
		try:
			data["covid_admissions_rate"] = await hass.async_add_executor_job(
				api.get_data, "COVID-19", "weekly_hospital_admissions_rate"
			)
		except UpdateFailed as err:
			_LOGGER.warning("Failed to fetch COVID-19 data: %s", err)
		
		# 2. Influenza Data (Hospital Admissions Rate)
		try:
			data["flu_admissions_rate"] = await hass.async_add_executor_job(
				api.get_data, "Influenza", "weekly_hospital_admissions_rate"
			)
		except UpdateFailed as err:
			_LOGGER.warning("Failed to fetch Influenza data: %s", err)
		
		# 3. Rhinovirus (Cold) Data (Lab Positivity)
		try:
			data["rhinovirus_positivity"] = await hass.async_add_executor_job(
				api.get_data, "OtherRespiratoryViruses", "rhinovirus_positive_count"
			)
		except UpdateFailed as err:
			_LOGGER.warning("Failed to fetch Rhinovirus data: %s", err)

		# Crucial check: If ALL fetches failed, raise UpdateFailed to mark integration unhealthy.
		if not any(data.values()):
			_LOGGER.error("All UKHSA data fetches failed.")
			raise UpdateFailed("All UKHSA data fetches failed.")
		
		return data

	coordinator = DataUpdateCoordinator(
		hass,
		_LOGGER,
		name="ukhsa_tracker_coordinator",
		update_method=async_update_data,
		update_interval=UPDATE_INTERVAL,
	)

	# Initial fetch of data
	await coordinator.async_config_entry_first_refresh()

	hass.data[DOMAIN][entry.entry_id] = coordinator

	# Set up the sensor platform
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

	return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
	"""Unload a config entry."""
	unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
	if unload_ok:
		hass.data[DOMAIN].pop(entry.entry_id)

	return unload_ok
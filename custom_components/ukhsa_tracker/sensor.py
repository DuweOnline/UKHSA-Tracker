# sensor.py

"""Platform for sensor entities."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfDataRate
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

# --- Sensor Definition List ---
SENSOR_TYPES = [
	{
		"key": "covid_admissions_rate",
		"name": "COVID-19 Hospital Admissions Rate",
		"unit": UnitOfDataRate.PER_100K_POPULATION,
		"icon": "mdi:hospital-box-outline",
	},
	{
		"key": "flu_admissions_rate",
		"name": "Influenza Hospital Admissions Rate",
		"unit": UnitOfDataRate.PER_100K_POPULATION,
		"icon": "mdi:thermometer-high",
	},
	{
		"key": "rhinovirus_positivity",
		"name": "Rhinovirus (Cold) Lab Positivity",
		"unit": PERCENTAGE,
		"icon": "mdi:microscope",
	},
]
# -----------------------------

async def async_setup_entry(hass, config_entry, async_add_entities):
	"""Set up the sensor platform."""
	coordinator = hass.data[DOMAIN][config_entry.entry_id]
	
	entities = []
	for sensor_type in SENSOR_TYPES:
		entities.append(UkhsaSensor(coordinator, sensor_type))
	
	async_add_entities(entities)

class UkhsaSensor(CoordinatorEntity, SensorEntity):
	"""Representation of an UKHSA Respiratory Sensor."""

	def __init__(self, coordinator, sensor_type):
		"""Initialize the sensor."""
		super().__init__(coordinator)
		self._key = sensor_type["key"]
		self._name = sensor_type["name"]
		self._attr_unit_of_measurement = sensor_type["unit"]
		self._attr_icon = sensor_type["icon"]
		
		# Unique ID for the sensor
		self._attr_unique_id = f"{DOMAIN}_{self._key}_england"
		
		# Friendly name for the entity
		self._attr_name = f"UKHSA {self._name}"
		
		# Device info for grouping sensors together
		self._attr_device_info = {
			"identifiers": {(DOMAIN, "ukhsa_respiratory_tracker")},
			"name": "UKHSA Respiratory Tracker",
			"manufacturer": "UK Health Security Agency",
			"model": "Respiratory Viruses",
		}

	@property
	def native_value(self):
		"""Return the state of the sensor."""
		data = self.coordinator.data.get(self._key)
		
		if data and data.get("value") is not None:
			# For percentage (e.g., Rhinovirus), convert to a roundable float
			if self._attr_unit_of_measurement == PERCENTAGE:
				return round(float(data["value"]), 1)
			
			# For rates, ensure it is a float
			return float(data["value"])
			
		return None

	@property
	def extra_state_attributes(self):
		"""Return the state attributes."""
		data = self.coordinator.data.get(self._key)
		
		if data:
			return {
				"date_of_report": data.get("date"),
				"geography": data.get("geography", "England"),
				"data_source": "UKHSA API",
			}
		return {}

	@property
	def device_class(self):
		"""Return the device class."""
		# Use measurement for all current sensors
		return SensorDeviceClass.MEASUREMENT
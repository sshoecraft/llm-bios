# Ecobee Thermostat API

The Ecobee thermostat is controlled via REST API.

## Authentication

All requests require an API key in the Authorization header.

## GET /thermostat

Returns: temperatureSetpoint, currentTemperature, mode, humidity

## How to Read Current Temperature

1. Obtain API key from Ecobee developer portal
2. Set Authorization header: Bearer {api_key}
3. GET /thermostat
4. Extract currentTemperature from response

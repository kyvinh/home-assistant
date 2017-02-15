"""Provide configuration end points for Z-Wave."""
import asyncio
import os
import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.components.zwave import DEVICE_CONFIG_SCHEMA_ENTRY
from homeassistant.util.yaml import load_yaml, dump


DEVICE_CONFIG = 'zwave_device_config.yaml'


@asyncio.coroutine
def async_setup(hass):
    """Setup the Z-Wave config API."""
    hass.http.register_view(DeviceConfigView)
    return True


class DeviceConfigView(HomeAssistantView):
    """Configure a Z-Wave device endpoint."""

    url = '/api/config/zwave/device_config/{entity_id}'
    name = 'api:config:zwave:device_config:update'

    @asyncio.coroutine
    def get(self, request, entity_id):
        """Fetch device specific config."""
        hass = request.app['hass']
        current = yield from hass.loop.run_in_executor(
            None, _read, hass.config.path(DEVICE_CONFIG))
        return self.json(current.get(entity_id, {}))

    @asyncio.coroutine
    def post(self, request, entity_id):
        """Validate config and return results."""
        try:
            data = yield from request.json()
        except ValueError:
            return self.json_message('Invalid JSON specified', 400)

        try:
            # We just validate, we don't store that data because
            # we don't want to store the defaults.
            DEVICE_CONFIG_SCHEMA_ENTRY(data)
        except vol.Invalid as err:
            print(data, err)
            return self.json_message('Message malformed: {}'.format(err), 400)

        hass = request.app['hass']
        path = hass.config.path(DEVICE_CONFIG)
        current = yield from hass.loop.run_in_executor(
            None, _read, hass.config.path(DEVICE_CONFIG))
        current.setdefault(entity_id, {}).update(data)

        yield from hass.loop.run_in_executor(
            None, _write, hass.config.path(path), current)

        return self.json({
            'result': 'ok',
        })


def _read(path):
    """Read YAML helper."""
    if not os.path.isfile(path):
        with open(path, 'w'):
            pass
        return {}

    return load_yaml(path)


def _write(path, data):
    """Write YAML helper."""
    with open(path, 'w') as outfile:
        dump(data, outfile)

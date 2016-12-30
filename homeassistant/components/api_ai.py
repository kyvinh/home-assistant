"""
API.AI webhook implementation for Home Assistant.

Inspired from API component.
"""
import asyncio
import json
import logging

from homeassistant.components.http import HomeAssistantView
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME, SERVICE_TURN_ON)
from homeassistant.helpers.state import AsyncTrackStates

DOMAIN = 'api_ai'
DEPENDENCIES = ['http']

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Register the API with the HTTP interface."""
    hass.http.register_view(APIAIWebhookView)
    return True


class APIAIWebhookView(HomeAssistantView):
    """View to handle API.AI webhook requests."""

    url = "/api_ai/webhook"
    name = "api_ai:webhook"

    @asyncio.coroutine
    def post(self, request):
        """Respond to webhook. Inspired from: https://github.com/api-ai/apiai-weather-webhook-sample/blob/master/app.py

        Returns a list of changed states.
        """
        hass = request.app['hass']
        body = yield from request.text()
        result = {}

        """Format of webhook JSON request: https://docs.api.ai/docs/query#response"""
        data = json.loads(body) if body else None

        # TODO Catch AttributeError: 'NoneType' object has no attribute 'get'
        #      in case there was a problem with the JSON response

        if data.get('result').get('action') == 'scene.activate':
            scene_to_activate = data.get('result').get('parameters').get('scene')
            _LOGGER.info('Activating scene %s', scene_to_activate)
            if scene_to_activate:
                with AsyncTrackStates(hass) as changed_states:
                    yield from hass.services.async_call(
                        'scene', SERVICE_TURN_ON, {ATTR_ENTITY_ID: 'scene.' + scene_to_activate}, True)
                result['data'] = self.json(changed_states)
            else:
                _LOGGER.warning('Could not process api.ai request: scene.activate called without scene name')

        result['data'] = []
        for state in changed_states:
            changed_state_string = 'Changed state: {} ({}) is now "{}"'.format(state.attributes[ATTR_FRIENDLY_NAME], state.entity_id, state.state)
            _LOGGER.info(changed_state_string)
            result['data'].append(changed_state_string)

        # TODO ALSO CATCH MISC. ERRORS!

        result['speech'] = "Request has been processed."
        return self.json(result)

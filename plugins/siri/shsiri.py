
from plugin import SiriPlugin

logger = logging.getLogger('')

class SmartHomeSiriPlugin(SiriPlugin):

    def __init__(self, smarthome):
        self._sh = smarthome

    def switch_bool(self, phrase, match_groups, item):
        logger.debug('switch state for item {0}'.format(item))
        m = match_groups[0].lower()
        item(m in ['an', 'ein', 'schliessen', 'runter'])
        response = 'OK'
        self.respond(response)
        self.complete()

    def trigger_logic(self, phrase, match_groups, logic):
        logger.debug('trigger logic {0}'.format(logic))
        logic()
        response = 'OK'
        self.respond(response)
        self.complete()

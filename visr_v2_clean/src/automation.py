"""
VIS-R v2 — Rule Engine
Evaluates risk and triggers TTS alerts + logging.
Includes cooldown to prevent alert spam.
"""
import time
from config import RISK_RULES


class RuleEngine:
    def __init__(self, tts_manager, logger):
        self.tts    = tts_manager
        self.logger = logger
        self._last_alert = {}   # risk_level -> last spoken time
        self._cooldown   = 8.0  # seconds between same-level alerts

    def evaluate(self, risk_level, description, suggested_action, frame=None):
        rule = RISK_RULES.get(risk_level, RISK_RULES['LOW'])

        if risk_level in ('HIGH', 'MEDIUM'):
            # Log always
            if rule.get('log', False):
                self.logger.log_event(risk_level, description, suggested_action, frame)

            # Speak with cooldown
            if rule.get('speak', False):
                last = self._last_alert.get(risk_level, 0)
                if time.time() - last > self._cooldown:
                    self._last_alert[risk_level] = time.time()
                    priority = (risk_level == 'HIGH')
                    if risk_level == 'HIGH':
                        msg = f"High risk alert. {description}. Recommended action: {suggested_action}"
                    else:
                        msg = f"Warning. {description}."
                    self.tts.speak(msg, priority=priority)

        return rule.get('action', 'none')

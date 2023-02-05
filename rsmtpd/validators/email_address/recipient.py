from abc import ABCMeta, abstractmethod
from logging import Logger
from rsmtpd.core.config_loader import ConfigLoader
from rsmtpd.validators.email_address.parser import ParsedEmailAddress
from typing import Dict, Union

# VALIDATION_RESULT values
# Email address is valid for delivery
VALID = "VALID"

# Email address is valid, but it is disabled at the moment
DISABLED = "DISABLED"

# Email address is undeliverable
INVALID = "INVALID"

# Email address is undeliverable, but can optionally be accepted for research or model training
# SOFT_INVALID must always be rejected during delivery
SOFT_INVALID = "SOFT_INVALID"

# Email address is undeliverable, and it is outside the domains we handle email for (useful for not forwarding errors)
INVALID_DOMAIN = "INVALID_DOMAIN"


class ValidatedRecipient(ParsedEmailAddress):
    def __init__(self, parsed_email_address: ParsedEmailAddress, validation_result: str = DISABLED,
                 deliver_to: Union[str, None] = None):
        super().__init__()
        self.is_valid = parsed_email_address.is_valid
        self.input = parsed_email_address.input
        self.email_address = parsed_email_address.email_address
        self.local_part = parsed_email_address.local_part
        self.domain = parsed_email_address.domain
        self.is_utf8 = parsed_email_address.is_utf8
        self.contained_rfc_brackets = parsed_email_address.contained_rfc_brackets
        self.validation_result: str = validation_result
        self.deliver_to: str = deliver_to or None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.email_address.lower() == other.email_address.lower()

    def __hash__(self):
        return hash(self.email_address.lower())


class RecipientValidator(metaclass=ABCMeta):
    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = "", default_config: Dict = {}):
        self._logger = logger
        self._config = config_loader.load(self, suffix=config_suffix, default=default_config)

    @abstractmethod
    def validate(self, parsed_email_address: ParsedEmailAddress) -> ValidatedRecipient:
        pass

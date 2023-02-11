from rsmtpd.validators.email_address.recipient import *
from typing import Dict, List, Union


class SimpleRecipientValidator(RecipientValidator):
    """
    A recipient validator that loads available domains and recipients from a YAMl config file
    """

    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = "", default_config: Dict = {}):
        super().__init__(logger, config_loader, config_suffix, default_config)
        self._domain_settings: Dict[str, Settings] = {}
        self._recipients: List[Recipient] = []
        self.__load_config()

    def validate(self, parsed_email_address: ParsedEmailAddress) -> ValidatedRecipient:
        if parsed_email_address.domain not in self._domain_settings:
            return ValidatedRecipient(parsed_email_address, INVALID_DOMAIN)

        for recipient in self._recipients:
            local_part_to_check = parsed_email_address.local_part.lower()
            if recipient.allow_tagging:
                for tagging_character in recipient.tagging_characters:
                    if tagging_character in local_part_to_check:
                        local_part_to_check = local_part_to_check[0:local_part_to_check.find(tagging_character)]
                        break

            if f"{local_part_to_check}@{parsed_email_address.domain}" == recipient.address:
                return ValidatedRecipient(parsed_email_address,
                                          VALID if recipient.enabled else DISABLED,
                                          recipient.deliver_to)

        validation_result = SOFT_INVALID if self._domain_settings[parsed_email_address.domain]\
            .allow_soft_delivery else INVALID
        return ValidatedRecipient(parsed_email_address, validation_result)

    def __load_config(self):
        global_settings = Settings(self._config)
        domains = self._config.get("domains", {})

        for domain, domain_dict in domains.items():
            domain_settings = Settings(domain_dict, global_settings)
            self._domain_settings[domain] = domain_settings

            for recipient_dict in domain_dict.get("recipients", []):
                recipient = Recipient(recipient_dict, domain, domain_settings)
                if recipient.address:
                    self._recipients.append(recipient)


class Settings:
    __allowed_tagging_characters = "!#$%&'*+-/=?^_`{|}~"

    def __init__(self, settings: Dict = None, defaults: 'Settings' = None):
        self.allow_soft_delivery: bool = False
        self.allow_tagging: bool = False
        self.tagging_characters: List[str] = []

        if settings is not None:
            if not defaults:
                defaults = Settings()

            self.allow_soft_delivery = bool(settings.get("allow_soft_delivery", defaults.allow_soft_delivery))
            self.allow_tagging = bool(settings.get("allow_tagging", defaults.allow_tagging))
            self.tagging_characters: List[str] = [char for char in
                                                  settings.get("tagging_characters",
                                                               "".join(defaults.tagging_characters))]
            for tagging_character in self.tagging_characters:
                if tagging_character not in self.__allowed_tagging_characters:
                    raise Exception(f"Invalid tagging character {tagging_character}; "
                                    f"(must be one of {self.__allowed_tagging_characters})")


class Recipient:
    def __init__(self, recipient_dict_or_str: Union[Dict, str], domain: str, domain_settings: Settings):
        if isinstance(recipient_dict_or_str, str):
            recipient = recipient_dict_or_str.lower()
            options = {}
        elif isinstance(recipient_dict_or_str, Dict):
            recipient = list(recipient_dict_or_str.keys())[0].lower()
            options = recipient_dict_or_str
        else:
            raise Exception("Recipient user detail must be a string or dictionary of key/value pairs")

        recipient_settings = Settings(options, domain_settings)

        self.address: str = f"{recipient}@{domain}"
        self.deliver_to: str = options.get("deliver_to", self.address)
        self.enabled: bool = bool(options.get("enabled", True))
        self.allow_tagging = recipient_settings.allow_tagging
        self.tagging_characters = recipient_settings.tagging_characters

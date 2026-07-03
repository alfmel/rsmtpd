import unittest
from rsmtpd.validators.email_address.parser import parse_email_address_input
from rsmtpd.validators.email_address.recipient import *
from rsmtpd.validators.email_address.simple_recipient_validator import SimpleRecipientValidator
from tests.mocks import MockConfigLoader, StubLoggerFactory
from typing import Dict, Union
from yaml import load, SafeLoader

full_yaml_config = """
allow_soft_delivery: no
allow_tagging: yes
tagging_characters: "+-"
domains:
  example.com:
    allow_soft_delivery: yes
    recipients:
      - postmaster:
        allow_tagging: no
      - alice
      - bob:
        tagging_characters: "+"
      - bob_jones:
        deliver_to: bob@example.com
  example.net:
    allow_tagging: no
    recipients:
      - postmaster
      - alice:
        allow_tagging: yes
      - bob:
        deliver_to: bob@example.com
      - eve:
        enabled: no 
"""


class TestSimpleAddressValidator(unittest.TestCase):
    def test_validate_base_addresses(self):
        validator = self.__getValidator(load(full_yaml_config, Loader=SafeLoader))

        self.__assertValidation(validator, "postmaster@example.com", VALID, "postmaster@example.com")
        self.__assertValidation(validator, "alice@example.com", VALID, "alice@example.com")
        self.__assertValidation(validator, "bob@example.com", VALID, "bob@example.com")

        self.__assertValidation(validator, "postmaster@example.net", VALID, "postmaster@example.net")
        self.__assertValidation(validator, "alice@example.net", VALID, "alice@example.net")
        self.__assertValidation(validator, "bob@example.net", VALID, "bob@example.com")
        self.__assertValidation(validator, "eve@example.net", DISABLED, "eve@example.net")

    def test_uppercase(self):
        validator = self.__getValidator(load(full_yaml_config, Loader=SafeLoader))
        self.__assertValidation(validator, "ALICE@EXAMPLE.COM", VALID, "alice@example.com")

    def test_tagging(self):
        validator = self.__getValidator(load(full_yaml_config, Loader=SafeLoader))

        self.__assertValidation(validator, "postmaster+tag@example.com", SOFT_INVALID, None)
        self.__assertValidation(validator, "alice+tag@example.com", VALID, "alice@example.com")
        self.__assertValidation(validator, "alice-tag@example.com", VALID, "alice@example.com")
        self.__assertValidation(validator, "bob+tag@example.com", VALID, "bob@example.com")
        self.__assertValidation(validator, "bob-tag@example.com", SOFT_INVALID, None)
        self.__assertValidation(validator, "bob_jones+tag@example.com", VALID, "bob@example.com")

        self.__assertValidation(validator, "postmaster+tag@example.net", INVALID, None)
        self.__assertValidation(validator, "alice+tag@example.net", VALID, "alice@example.net")
        self.__assertValidation(validator, "bob+tag@example.net", INVALID, None)
        self.__assertValidation(validator, "eve+tag@example.net", INVALID, None)

    def test_aliases(self):
        validator = self.__getValidator(load(full_yaml_config, Loader=SafeLoader))
        self.__assertValidation(validator, "bob_jones@example.com", VALID, "bob@example.com")
        self.__assertValidation(validator, "bob@example.net", VALID, "bob@example.com")

    def test_domains(self):
        validator = self.__getValidator(load(full_yaml_config, Loader=SafeLoader))
        self.__assertValidation(validator, "somebody@example.com", SOFT_INVALID, None)
        self.__assertValidation(validator, "somebody@example.net", INVALID, None)
        self.__assertValidation(validator, "somebody@example.org", INVALID_DOMAIN, None)

    def __assertValidation(self, validator: SimpleRecipientValidator, email_address: str, validation_result: str,
                           deliver_to: Union[str, None]) -> None:
        parsed_email_address = parse_email_address_input(f"<{email_address}>")
        result = validator.validate(parsed_email_address)
        self.assertEqual(validation_result, result.validation_result)
        self.assertEqual(deliver_to, result.deliver_to)

    def __getValidator(self, config: Dict) -> SimpleRecipientValidator:
        mock_logger = StubLoggerFactory().get_module_logger(None)
        mock_config_loader = MockConfigLoader(StubLoggerFactory())
        return SimpleRecipientValidator(mock_logger, mock_config_loader, "", config)


if __name__ == '__main__':
    unittest.main()

from rsmtpd.handlers.base_command import BaseCommand
from rsmtpd.handlers.shared_state import SharedState
from rsmtpd.response.base_response import BaseResponse
from rsmtpd.response.smtp_250 import SmtpResponse250
from rsmtpd.response.smtp_501 import SmtpResponse501
from rsmtpd.response.smtp_503 import SmtpResponse503
from rsmtpd.response.smtp_504 import SmtpResponse504
from rsmtpd.response.smtp_550 import SmtpResponse550
from rsmtpd.validators.email_address.parser import parse_email_address_input
from rsmtpd.validators.email_address.recipient import *
from rsmtpd.validators.email_address.simple_recipient_validator import SimpleRecipientValidator


class RecipientHandler(BaseCommand):
    """
    The built-in command handler for the RCPT command (only handles RCPT TO)
    """

    # TODO: Inject Recipient Validator via factory
    def __init__(self, logger: Logger, config_loader: ConfigLoader, config_suffix: str = "", default_config: Dict = {},
                 recipient_validator: RecipientValidator = None):
        super().__init__(logger, config_loader, config_suffix, default_config)
        if not recipient_validator:
            recipient_validator = SimpleRecipientValidator(logger, config_loader, config_suffix)
        self._recipient_validator = recipient_validator

    def handle(self, command: str, argument: str, shared_state: SharedState) -> BaseResponse:
        if shared_state.client_name is None:
            return SmtpResponse503("You must say HELO/EHLO before using this command")

        if not argument.upper().startswith("TO:"):
            return SmtpResponse504("Only RCPT TO> is implemented on this server")

        parsed_email_address = parse_email_address_input(argument.split(":", 1)[1])

        if not parsed_email_address.is_valid:
            return SmtpResponse501("Email address does not appear to be valid")

        validated_recipient = self._recipient_validator.validate(parsed_email_address)
        self._logger.info(f"Recipient <{parsed_email_address.email_address}> validation result: "
                          f"{validated_recipient.validation_result}")

        if validated_recipient.validation_result == VALID or validated_recipient.validation_result == SOFT_INVALID:
            shared_state.recipients.add(validated_recipient)
            return SmtpResponse250()

        if validated_recipient.validation_result == DISABLED:
            return SmtpResponse550("This recipient no longer exists")

        if validated_recipient.validation_result == INVALID_DOMAIN:
            return SmtpResponse550("Relaying not allowed")

        return SmtpResponse550("Invalid recipient")

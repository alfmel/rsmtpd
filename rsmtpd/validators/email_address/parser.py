import re
from typing import Union


class ParsedEmailAddress:
    def __init__(self):
        # Whether the email address is valid (local part + domain)
        self.is_valid: bool = False

        # The raw input as sent by the client
        self.input: Union[str, None] = None

        # The email address without name or brackets
        self.email_address: Union[str, None] = None

        # The local part of the email address
        self.local_part: Union[str, None] = None

        # The domain of the email address
        self.domain: Union[str, None] = None

        # Whether the email address was UTF8-encoded
        self.is_utf8: bool = False

        # Whether the email address was properly formatted with the <> brackets
        self.contained_rfc_brackets: bool = False


def parse_email_address_input(email_address_input: str, allow_empty=False) -> ParsedEmailAddress:
    result = ParsedEmailAddress()
    if email_address_input.endswith(" SMTPUTF8"):  # Note space at start to conform with RFC 6531
        result.is_utf8 = True
        email_address_input = email_address_input.replace(" SMTPUTF8", "").strip()

    result.input = email_address_input

    if re.search(r"(?<!\\)<(.*)(?<!\\)>", email_address_input):
        result.contained_rfc_brackets = True
        result.email_address = email_address_input[email_address_input.find("<") + 1:email_address_input.rfind(">")]
    else:
        result.email_address = email_address_input.strip()

    at_sign_location = result.email_address.rfind("@")
    if at_sign_location != -1:
        result.local_part = result.email_address[0:at_sign_location]
        result.domain = result.email_address[at_sign_location + 1:].lower()

        result.is_valid = validate_domain(result.domain) and validate_local_part(result.local_part)
    else:
        result.local_part = result.email_address

    if result.email_address == "" and allow_empty:
        # This allows us to receive bounced emails.
        result.is_valid = True

    return result


def validate_domain(domain: str) -> bool:
    if ".." in domain:
        return False
    if "_" in domain:
        return False
    return bool(re.match(r"^\w[\w.-]+\w+$", domain))


def validate_local_part(local_part: str) -> bool:
    if len(local_part) == 0 or local_part == '""':
        return False
    if local_part.startswith('"') and local_part.endswith('"'):
        return True
    if ".." in local_part:
        return False
    if re.search(r"(?<!\\)[@\\ ]", local_part):
        return False

    return True

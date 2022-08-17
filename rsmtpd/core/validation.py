import re


class EmailAddressParseResult:
    # Whether the email address is valid (local part + domain)
    is_valid: bool = False

    # The input given to validator, without extensions
    input: str = None

    # The email address without name or brackets
    email_address: str = None

    # The local part of the email address
    local_part: str = None

    # The domain of the email address
    domain: str = None

    # Whether the email address was UTF8-encoded
    is_utf8: bool = False

    # Whether the email address was properly formatted with the <> brackets
    contained_rfc_brackets: bool = False


class EmailAddressVerificationResult(EmailAddressParseResult):
    # Whether the email address is deliverable (None means it has not been verified)
    is_deliverable: bool = None

    def __init__(self, email_address_parse_result: EmailAddressParseResult, is_deliverable: bool = False):
        self.is_valid = email_address_parse_result.is_valid
        self.input = email_address_parse_result.input
        self.email_address = email_address_parse_result.email_address
        self.local_part = email_address_parse_result.local_part
        self.domain = email_address_parse_result.domain
        self.is_utf8 = email_address_parse_result.is_utf8
        self.contained_rfc_brackets = email_address_parse_result.contained_rfc_brackets
        self.is_deliverable = is_deliverable

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.email_address.lower() == other.email_address.lower()

    def __hash__(self):
        return hash(self.email_address.lower())


def parse_email_address_input(email_address_input: str) -> EmailAddressParseResult:
    result = EmailAddressParseResult()
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
        result.domain = result.email_address[at_sign_location + 1:]

        result.is_valid = validate_domain(result.domain) and validate_local_part(result.local_part)
    else:
        result.local_part = result.email_address

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

from rsmtpd.validators.email_address.parser import ParsedEmailAddress


class ValidatedRecipient(ParsedEmailAddress):
    def __init__(self, email_address_parse_result: ParsedEmailAddress, is_deliverable: bool = False):
        super().__init__()
        self.is_valid = email_address_parse_result.is_valid
        self.input = email_address_parse_result.input
        self.email_address = email_address_parse_result.email_address
        self.local_part = email_address_parse_result.local_part
        self.domain = email_address_parse_result.domain
        self.is_utf8 = email_address_parse_result.is_utf8
        self.contained_rfc_brackets = email_address_parse_result.contained_rfc_brackets

        # Whether the email address is deliverable
        self.is_deliverable: bool = is_deliverable

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.email_address.lower() == other.email_address.lower()

    def __hash__(self):
        return hash(self.email_address.lower())

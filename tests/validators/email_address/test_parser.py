import unittest
from rsmtpd.validators.email_address.parser import *


class TestParseEmailAddressInput(unittest.TestCase):
    def test_standard_entry(self):
        result = parse_email_address_input("<first.last@example.com>")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.input, "<first.last@example.com>")
        self.assertEqual(result.email_address, "first.last@example.com")
        self.assertEqual(result.local_part, "first.last")
        self.assertEqual(result.domain, "example.com")
        self.assertFalse(result.is_utf8)
        self.assertTrue(result.contained_rfc_brackets)

    def test_utf8_entry(self):
        result = parse_email_address_input("<áñö@example.com> SMTPUTF8")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.input, "<áñö@example.com>")
        self.assertEqual(result.email_address, "áñö@example.com")
        self.assertEqual(result.local_part, "áñö")
        self.assertEqual(result.domain, "example.com")
        self.assertTrue(result.is_utf8)
        self.assertTrue(result.contained_rfc_brackets)

    def test_standard_entry_without_brackets(self):
        result = parse_email_address_input("first.last@example.com")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.input, "first.last@example.com")
        self.assertEqual(result.email_address, "first.last@example.com")
        self.assertEqual(result.local_part, "first.last")
        self.assertEqual(result.domain, "example.com")
        self.assertFalse(result.is_utf8)
        self.assertFalse(result.contained_rfc_brackets)

    def test_with_name(self):
        result = parse_email_address_input("First and Last <first.last@example.com>")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.input, "First and Last <first.last@example.com>")
        self.assertEqual(result.email_address, "first.last@example.com")
        self.assertEqual(result.local_part, "first.last")
        self.assertEqual(result.domain, "example.com")
        self.assertFalse(result.is_utf8)
        self.assertTrue(result.contained_rfc_brackets)

    def test_without_domain(self):
        result = parse_email_address_input("<first.last>")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.input, "<first.last>")
        self.assertEqual(result.email_address, "first.last")
        self.assertEqual(result.local_part, "first.last")
        self.assertIsNone(result.domain)
        self.assertFalse(result.is_utf8)
        self.assertTrue(result.contained_rfc_brackets)

    def test_without_local_part(self):
        result = parse_email_address_input("@example.com")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.input, "@example.com")
        self.assertEqual(result.email_address, "@example.com")
        self.assertEqual(result.local_part, "")
        self.assertEqual(result.domain, "example.com")
        self.assertFalse(result.is_utf8)
        self.assertFalse(result.contained_rfc_brackets)

    def test_empty_address(self):
        result = parse_email_address_input("<>")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.input, "<>")
        self.assertEqual(result.email_address, "")
        self.assertEqual(result.local_part, "")
        self.assertEqual(result.domain, None)
        self.assertFalse(result.is_utf8)
        self.assertTrue(result.contained_rfc_brackets)

    def test_empty_address_allow_empty(self):
        result = parse_email_address_input("<>", True)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.input, "<>")
        self.assertEqual(result.email_address, "")
        self.assertEqual(result.local_part, "")
        self.assertEqual(result.domain, None)
        self.assertFalse(result.is_utf8)
        self.assertTrue(result.contained_rfc_brackets)


class TestValidateDomain(unittest.TestCase):
    def test_validate_domain(self):
        self.assertTrue(validate_domain("example.com"))
        self.assertTrue(validate_domain("subdomain.example.com"))
        self.assertTrue(validate_domain("123xyz.example.com"))
        self.assertTrue(validate_domain("good-ok.example.com"))
        self.assertTrue(validate_domain("tld"))  # Future-proof for stand-alone vanity TLDs
        self.assertTrue(validate_domain("áñö.co"))

        self.assertFalse(validate_domain(""))
        self.assertFalse(validate_domain("bad..com"))
        self.assertFalse(validate_domain(".bad.com"))
        self.assertFalse(validate_domain("bad.com."))
        self.assertFalse(validate_domain("bad_domain.com"))
        self.assertFalse(validate_domain("bad domain.com"))
        self.assertFalse(validate_domain("bad_domain.com"))
        self.assertFalse(validate_domain("bad|domain.com"))
        self.assertFalse(validate_domain("bad/domain.com"))
        self.assertFalse(validate_domain("bad\\domain.com"))
        self.assertFalse(validate_domain("bad\tdomain.com"))
        self.assertFalse(validate_domain("bad\ndomain.com"))


class TestValidateLocalPart(unittest.TestCase):
    def test_validate_local_part(self):
        # Tests based on RFC 3696 Section 3
        # TODO: Fix last remaining cases (not quite perfect, but we are getting there)
        self.assertTrue(validate_local_part("first"))
        self.assertTrue(validate_local_part("first_last"))
        self.assertTrue(validate_local_part("first.last"))
        self.assertTrue(validate_local_part("first-last"))
        self.assertTrue(validate_local_part("first+last"))
        self.assertTrue(validate_local_part("first1"))
        self.assertTrue(validate_local_part("first(last)"))
        self.assertTrue(validate_local_part("first[last]"))
        self.assertTrue(validate_local_part("first{last}"))
        self.assertTrue(validate_local_part("first!last"))
        self.assertTrue(validate_local_part("first#last"))
        self.assertTrue(validate_local_part("first$last"))
        self.assertTrue(validate_local_part("first%last"))
        self.assertTrue(validate_local_part("first&last"))
        self.assertTrue(validate_local_part("first'last"))
        self.assertTrue(validate_local_part("first`last"))
        self.assertTrue(validate_local_part("first*last"))
        self.assertTrue(validate_local_part("first=last"))
        self.assertTrue(validate_local_part("first~last"))
        self.assertTrue(validate_local_part("first|last"))
        self.assertTrue(validate_local_part("first?last"))
        self.assertTrue(validate_local_part("first^last"))
        self.assertTrue(validate_local_part("first/last"))
        self.assertTrue(validate_local_part("fírst/lást"))
        # self.assertTrue(validate_local_part("first\\\\last"))
        # self.assertTrue(validate_local_part("first\\ last"))
        # self.assertTrue(validate_local_part("first\\@last"))
        # self.assertTrue(validate_local_part("first\\@last"))

        self.assertFalse(validate_local_part(""))
        self.assertFalse(validate_local_part("first\\last"))
        self.assertFalse(validate_local_part("first last"))
        self.assertFalse(validate_local_part("first@last"))
        self.assertFalse(validate_local_part("first..last"))
        # self.assertFalse(validate_local_part("first\"last"))
        # self.assertFalse(validate_local_part("first(last)"))
        # self.assertFalse(validate_local_part("first{last}"))

    def test_validate_quoted_local_part(self):
        # Tests based on RFC 3696 Section 3
        self.assertTrue(validate_local_part('"quoted@local"'))
        self.assertFalse(validate_local_part('""'))


if __name__ == '__main__':
    unittest.main()

import unittest
from rsmtpd.validators.domain import dns


class TestDns(unittest.TestCase):
    def test_by_name(self):
        result = dns.by_name("github.com")
        self.assertRegex(result, r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

    def test_by_name_no_result(self):
        result = dns.by_name("should-not-exist.example.com")
        self.assertIsNone(result)

    def test_by_ip(self):
        ip = dns.by_name("github.com")
        host = dns.by_ip(ip)
        self.assertTrue("github.com" in host)

    def test_by_ip_no_result(self):
        result = dns.by_ip("127.1.1.1")
        self.assertIsNone(result)

    def test_find_best_ip_empty_list(self):
        result = dns._find_best_ip([], "10.20.30.40")
        self.assertIsNone(result)

    def test_find_best_ip_exact_match(self):
        ips = ["10.20.30.40", "10.20.35.40", "10.20.30.100"]

        result = dns._find_best_ip(ips, "10.20.30.40")
        self.assertEqual(result, "10.20.30.40")

        result = dns._find_best_ip(ips, "10.20.30.100")
        self.assertEqual(result, "10.20.30.100")

    def test_find_best_ip_closest_match(self):
        ips = ["10.20.30.40", "10.20.35.40", "10.20.30.100"]

        result = dns._find_best_ip(ips, "10.20.30.80")
        self.assertEqual(result, "10.20.30.100")

        result = dns._find_best_ip(ips, "10.20.33.40")
        self.assertEqual(result, "10.20.35.40")

    def test_find_best_ip_no_match(self):
        ips = ["10.20.30.40", "10.20.35.40", "10.20.30.100"]
        result = dns._find_best_ip(ips, "192.168.0.1")
        self.assertTrue(result in ips)

    def test_find_best_fqdn_empty_list(self):
        result = dns._find_best_fqdn([], "smtp.example.com")
        self.assertIsNone(result)

    def test_find_best_fqdn_exact_match(self):
        domains = ["www.example.com", "smtp.example.com", "example.com", "host.example.net"]

        result = dns._find_best_fqdn(domains, "smtp.example.com")
        self.assertEqual(result, "smtp.example.com")

        result = dns._find_best_fqdn(domains, "example.com")
        self.assertEqual(result, "example.com")

        result = dns._find_best_fqdn(domains, "host.example.net")
        self.assertEqual(result, "host.example.net")

    # Future version, perhaps
    # def test_find_best_fqdn_closest_match(self):
    #     domains = ["www.example.com", "smtp.example.com", "example.com", "host.example.net"]
    #
    #     result = dns._find_best_fqdn(domains, "smtp1.example.com")
    #     self.assertEqual(result, "smtp.example.com")
    #
    #     result = dns._find_best_fqdn(domains, "host-a.example.net")
    #     self.assertEqual(result, "host.example.net")

    def test_find_best_fqdn_no_match(self):
        domains = ["www.example.com", "smtp.example.com", "example.com", "host.example.net"]
        result = dns._find_best_fqdn(domains, "smtp.example.com")
        self.assertTrue(result in domains)

    def test_mx_records(self):
        results = dns.mx_records("gmail.com")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertTrue(result.endswith("google.com"))

    def test_mx_records_no_results(self):
        results = dns.mx_records("does-not-exist.example.com")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_get_domain_age_in_days(self):
        age = dns.get_domain_age_in_days("example.com")
        self.assertGreater(age, 3650)

    def test_get_domain_age_in_days_non_existent_domain(self):
        age = dns.get_domain_age_in_days("this-domain-should-not-exist.com")
        self.assertEqual(age, 0)


if __name__ == '__main__':
    unittest.main()

from dns import resolver, reversename
from typing import List, Union

from dns.resolver import NXDOMAIN


def by_name(fqdn: str, ip_address_hint: str = None) -> Union[str, None]:
    try:
        result = resolver.resolve(fqdn, "A")
        ips = [answer.address for answer in result]
    except NXDOMAIN:
        return None
    except Exception:
        return None

    if not ip_address_hint:
        return ips[0]

    return _find_best_ip(ips, ip_address_hint)


def by_ip(ip_address: str, domain_hint: str = None) -> Union[str, None]:
    try:
        reverse_lookup = reversename.from_address(ip_address)
        result = resolver.resolve(str(reverse_lookup), "PTR")
        domains = [str(answer) for answer in result]
    except NXDOMAIN:
        return None
    except Exception:
        return None

    if not domain_hint:
        return domains[0]

    return _find_best_fqdn(domains, domain_hint)


def mx_records(domain: str) -> List[str]:
    try:
        results = resolver.resolve(domain, "MX")
        return [str(result.exchange)[:-1] for result in results]
    except NXDOMAIN:
        return []


def _find_best_ip(ip_addresses: List[str], ip_address: str) -> Union[str, None]:
    if not len(ip_addresses):
        return None

    ip_value = __ip_to_numerical_value(ip_address)
    differences = [{"ip": ip, "diff": abs(ip_value - __ip_to_numerical_value(ip))} for ip in ip_addresses]
    sorted_differences = sorted(differences, key=lambda e: e["diff"])
    return sorted_differences[0]["ip"]


def _find_best_fqdn(domains: List[str], domain: str) -> Union[str, None]:
    if not len(domains):
        return None

    for d in domains:
        if d.lower() == domain.lower():
            return d.lower()

    level_matches = [{"domain": d.lower(), "match": __domain_level_matches(domain.lower(), d.lower())} for d in domains]
    sorted_level_matches = sorted(level_matches, key=lambda e: e["match"])
    sorted_level_matches.reverse()

    return sorted_level_matches[0]["domain"]


def __ip_to_numerical_value(ip_address: str) -> int:
    values = ip_address.split(".")
    return int(values[0]) * 256**3 + int(values[1]) * 256**2 + int(values[2]) * 256 + int(values[3])


def __domain_level_matches(domain1: str, domain2: str) -> int:
    domain1_parts = domain1.split(".")
    domain2_parts = domain2.split(".")

    domain1_parts.reverse()
    domain2_parts.reverse()

    if len(domain1_parts) > len(domain2_parts):
        long_domain = domain1_parts
        short_domain = domain2_parts
    else:
        long_domain = domain2_parts
        short_domain = domain1_parts

    for i in range(0, len(short_domain)):
        if short_domain[i] != long_domain[i]:
            return i

    return len(short_domain)

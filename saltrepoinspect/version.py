import re
import requests
from bs4 import BeautifulSoup


def parse_version(version):
    exp = '(?P<vendor>sles|rhel)(?P<major>\d{1,})(?:(?P<sp>sp)(?P<minor>\d{1,}))*'
    return re.match(exp, version).groups()


def parse_flavor(flavor):
    flavor_major = None
    flavor_minor = None

    if flavor == 'devel':
        # devel means install salt from git repository
        # and because there are no OBS repositories for it
        # we treat it as products so that we don't break the templates commands
        flavor_major = 'products'
    else:
        flavor_major, flavor_minor = flavor.split('-') if '-' in  flavor else (flavor, None)

    return flavor_major, flavor_minor


def get_salt_version(repo_url):
    resp = requests.get("{0}/x86_64".format(repo_url))
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    ex = re.compile(r'^salt-(?P<version>[0-9a-z-\.]+)-(?P<build>[0-9\.]+).x86_64.rpm')
    salt = soup.find('a', href=ex)
    match = ex.match(salt.text)
    return match.groupdict()['version']


def get_repo_parts(version):
    vendor, version_major, separator, version_minor = parse_version(version)
    repo_parts = [version_major]
    if version_minor:
        repo_parts.append('{}{}'.format(separator, version_minor))
    return repo_parts


def get_repo_name(version, flavor):
    vendor, version_major, separator, version_minor = parse_version(version)
    repo_parts = get_repo_parts(version)
    if vendor == 'SLES' and version_major == '11':
        repo_name = 'SLE_11_SP4'
    else:
        repo_name = '_'.join(repo_parts)
    return repo_name


def get_salt_repo_name(version, vendor, repo_name):
    salt_repo_name = 'SLE_{}'.format(repo_name).upper()
    if vendor == 'rhel':
        salt_repo_name = '{}_{}'.format(vendor, repo_name)

    if version in ['sles11sp3', 'sles11sp4']:
        salt_repo_name = 'SLE_11_SP4'

    return salt_repo_name


def get_salt_repo_url_flavor(flavor):
    flavor_major, flavor_minor = parse_flavor(flavor)
    salt_repo_url_parts = [flavor_major]
    if flavor_minor:
        salt_repo_url_parts.append(flavor_minor)
    salt_repo_url_flavor = ':/'.join(salt_repo_url_parts)
    return salt_repo_url_flavor



def get_salt_repo_url(version, flavor):
    vendor, version_major, separator, version_minor = parse_version(version)
    salt_repo_url_flavor = get_salt_repo_url_flavor(flavor)
    salt_repo_name = get_salt_repo_name(version, vendor, get_repo_name(version, flavor))
    salt_repo_url = (
        "http://download.opensuse.org/repositories/"
        "systemsmanagement:/saltstack:/{0}/{1}/".format(
            salt_repo_url_flavor, salt_repo_name.upper())
    )
    return salt_repo_url

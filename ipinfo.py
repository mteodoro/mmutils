import os
import socket
import struct

try:
    from collections import namedtuple
except ImportError:
    #http://code.activestate.com/recipes/500261-named-tuples/
    from namedtuple import namedtuple

try:
    import GeoIP as geoip
    GEOIP_MEMORY_CACHE = geoip.GEOIP_MEMORY_CACHE
    GEOIP_STANDARD = geoip.GEOIP_STANDARD
    _geo_open = geoip.open
except ImportError:
    import pygeoip as geoip
    GEOIP_MEMORY_CACHE = geoip.MEMORY_CACHE
    GEOIP_STANDARD = geoip.STANDARD
    _geo_open = geoip.GeoIP

__all__ = ['init_geo', 'init_asn', 'get_geo', 'get_asn']


search_paths = ['.', '/usr/local/share/GeoIP', '/usr/share/GeoIP']
def _init(db, flags):
    for path in search_paths:
        dbpath = os.path.join(path, db)
        if os.path.exists(dbpath):
            return _geo_open(dbpath, flags)

_gic = None
def init_geo(db='GeoIPCity.dat', flags=GEOIP_MEMORY_CACHE):
    global _gic
    _gic = _init(db, flags)

_gia = None
def init_asn(db='GeoIPASNum.dat', flags=GEOIP_MEMORY_CACHE):
    global _gia
    _gia = _init(db, flags)


_geo_default = {
    'area_code': 0,
    'city': u'',
    'continent': u'',
    'country_code': u'',
    'country_code3': u'',
    'country_name': u'',
    'dma_code': 0,
    'latitude': 0.0,
    'longitude': 0.0,
    'metro_code': 0,
    'postal_code': u'',
    'region': u'',
    'region_code': u'',
    'time_zone': u''
}
_geo_str_keys = set(k for k,v in _geo_default.iteritems() if v == u'')

IpGeo = namedtuple('IpGeo', sorted(_geo_default))
ipgeo_default = IpGeo(**_geo_default)

def get_geo(ip):
    if not _gic: init_geo()

    rec = _gic.record_by_addr(ip)
    if not rec:
        return ipgeo_default

    for k in _geo_str_keys:
        v = rec.get(k) or ''
        rec[k] = v.decode('latin1')

    #fixup - pygeoip exposes region as region_code
    if not rec['region']:
        rec['region'] = rec['region_code']
    return IpGeo(**rec)


IpAsn = namedtuple('IpAsn', ['asn', 'asname'])
ipasn_default = IpAsn(0, u'')

def get_asn(ip):
    if not _gia: init_asn()

    try:
        rec = _gia.org_by_addr(ip)
        asn, asname = rec.split(' ', 1)
        return IpAsn(int(asn[2:]), asname.decode('latin1'))
    except Exception, e:
        return ipasn_default


def ip2int(ip):
    return struct.unpack("!I", socket.inet_aton(ip))[0]


def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I", ip))


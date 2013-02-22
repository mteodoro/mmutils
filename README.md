mmutils
=======

Tools for working with MaxMind GeoIP csv and dat files

ipinfo.py: convenience wrapper for GeoIPCity and GeoIPASNum databases

Use init_geo or init_asn to override default db locations and flags.

Example:
    >>> import ipinfo
    >>> ipinfo.get_geo('8.8.8.8')
    IpGeo(area_code=650, city=u'Mountain View', country_code=u'US', country_code3=u'USA', country_name=u'United States', dma_code=807, latitude=37.419200897216797, longitude=-122.05740356445312, metro_code=807, postal_code=u'94043', region=u'CA', region_name=u'California', time_zone=u'America/Los_Angeles')
    >>> ipinfo.get_asn('8.8.8.8')
    IpAsn(asn=15169, asname=u'Google Inc.')


mmutils
=======

Tools for working with MaxMind GeoIP csv and dat files
------------------------------------------------------

**ipinfo.py**: Convenience wrapper for GeoIPCity and GeoIPASNum databases.  Use init\_geo or init\_asn to override default db locations and flags.

Example:

    >>> import ipinfo
    >>> ipinfo.get_geo('8.8.8.8')
    IpGeo(area_code=650, city=u'Mountain View', country_code=u'US', country_code3=u'USA', country_name=u'United States', dma_code=807, latitude=37.419200897216797, longitude=-122.05740356445312, metro_code=807, postal_code=u'94043', region=u'CA', region_name=u'California', time_zone=u'America/Los_Angeles')
    >>> ipinfo.get_asn('8.8.8.8')
    IpAsn(asn=15169, asname=u'Google Inc.')


**csv2dat.py**: Converts MaxMind CSV files to .dat files.  Useful for augmenting MaxMind data.  Currently supports GeoIP City and ASN database types, for *IPv4 only*.  Note: runs 4-5x faster under pypy.

Examples:

Convert MaxMind ASN CSV to .dat format:

    $ cat GeoIPASNum2.csv | pypy ./csv2dat.py -w mmasn.dat mmasn
    wrote 356311-node trie with 285539 networks (42664 distinct labels) in 3 seconds

Test mmasn.dat file against list of IPs, one per line:

    $ cat ips.txt | pypy ./csv2dat.py test asn GeoIPASNum.dat mmasn.dat
    using pygeoip module
    ok: 670135 bad: 0

Convert MaxMind City files to .dat format:

    $ cat GeoLiteCity-Blocks.csv | pypy ./csv2dat.py -w mmcity.dat -l GeoLiteCity-Location.csv mmcity
    wrote 2943570-node trie with 2939800 networks (109370 distinct labels) in 36 seconds

Test mmcity.dat file against list of IPs, one per line:

    $ cat ips.txt | pypy ./csv2dat.py test city GeoLiteCity.dat mmcity.dat
    using pygeoip module
    ok: 670135 bad: 0

Flatten MaxMind City CSVs into one file (for easier editing):

    $ cat GeoLiteCity-Blocks.csv | pypy ./csv2dat.py -w mmcityX.dat -l GeoLiteCity-Location.csv flat > mmcity_flat.csv

Convert flattened MaxMind City files to .dat format:

    $ cat mmcity_flat.csv | pypy ./csv2dat.py -w mmcity.dat  mmcity
    wrote 2943570-node trie with 2939800 networks (109370 distinct labels) in 36 seconds

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


**csv2dat.py**: Converts MaxMind CSV files to .dat files.  Useful for augmenting MaxMind data.  Currently supports GeoIP City and ASN database types.  Note: runs 4-5x faster under pypy.

Examples:

Convert MaxMind ASN CSV to .dat format:

    $ csv2dat.py -w mmasn.dat mmasn GeoIPASNum2.csv
    wrote 356311-node trie with 285539 networks (42664 distinct labels) in 3 seconds

Test mmasn.dat file against list of IPs, one per line:

    $ csv2dat.py test GeoIPASNum.dat mmasn.dat ips.txt
    ok: 670135 bad: 0

Convert MaxMind City files to .dat format:

    $ csv2dat.py -w mmcity.dat -l GeoLiteCity-Location.csv mmcity GeoLiteCity-Blocks.csv
    wrote 2943570-node trie with 2939800 networks (109370 distinct labels) in 36 seconds

Test mmcity.dat file against list of IPs, one per line:

    $ csv2dat.py test GeoLiteCity.dat mmcity.dat ips.txt
    ok: 670135 bad: 0

Flatten MaxMind City CSVs into one file (for easier editing):

    $ csv2dat.py -l GeoLiteCity-Location.csv flat GeoLiteCity-Blocks.csv > mmcity_flat.csv

Convert flattened MaxMind City files to .dat format:

    $ csv2dat.py -w mmcity.dat mmcity flatcity.csv
    wrote 2943570-node trie with 2939800 networks (109370 distinct labels) in 36 seconds

Convert MaxMind ASN v6 CSV to .dat format:

    $ csv2dat.py -w mmasn6.dat mmasn6 GeoIPASNum2v6.csv
    wrote 63125-node trie with 35983 networks (6737 distinct labels) in 2 seconds

Convert MaxMind City v6 CSV to .dat format:

    $ csv2dat.py -w mmcity6.dat mmcity6 GeoLiteCityv6.csv
    wrote 80637-node trie with 13074 networks (205 distinct labels) in 2 seconds

Convert MaxMind Country CSV to .dat format:

    $ csv2dat.py -w mmcountry.dat mmcountry GeoIPCountryWhois.csv
    wrote 136109-node trie with 133498 networks (250 distinct labels) in 8 seconds

Convert MaxMind Country v6 CSV to .dat format:

    $ csv2dat.py -w mmcountry6.dat mmcountry6 GeoIPv6.csv
    wrote 102601-node trie with 17580 networks (215 distinct labels) in 3 seconds

Convert MaxMind ISP CSV to .dat format:
    $ csv2dat.py -w mmisp.dat mmisp GeoIPISP.csv
    wrote 378619-node trie with 303605 networks (45963 distinct labels) in 19 seconds

Convert MaxMind Org CSV to .dat format:
    $ csv2dat.py -w mmorg.dat mmorg GeoIPOrg.csv
    wrote 378619-node trie with 303605 networks (45963 distinct labels) in 19 seconds


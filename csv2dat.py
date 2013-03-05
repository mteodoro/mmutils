#!/usr/bin/env python
import sys
import logging
import logging.handlers
import optparse

import csv
import fileinput
import itertools
import struct
import time

from functools import partial

import ipaddr
import pygeoip

#NOTE: This list needs to be kept in sync with GeoIP_country_code in
#https://raw.github.com/maxmind/geoip-api-c/master/libGeoIP/GeoIP.c
GeoIP_country_code = [
    "--","AP","EU","AD","AE","AF","AG","AI","AL","AM","CW",
    "AO","AQ","AR","AS","AT","AU","AW","AZ","BA","BB",
    "BD","BE","BF","BG","BH","BI","BJ","BM","BN","BO",
    "BR","BS","BT","BV","BW","BY","BZ","CA","CC","CD",
    "CF","CG","CH","CI","CK","CL","CM","CN","CO","CR",
    "CU","CV","CX","CY","CZ","DE","DJ","DK","DM","DO",
    "DZ","EC","EE","EG","EH","ER","ES","ET","FI","FJ",
    "FK","FM","FO","FR","SX","GA","GB","GD","GE","GF",
    "GH","GI","GL","GM","GN","GP","GQ","GR","GS","GT",
    "GU","GW","GY","HK","HM","HN","HR","HT","HU","ID",
    "IE","IL","IN","IO","IQ","IR","IS","IT","JM","JO",
    "JP","KE","KG","KH","KI","KM","KN","KP","KR","KW",
    "KY","KZ","LA","LB","LC","LI","LK","LR","LS","LT",
    "LU","LV","LY","MA","MC","MD","MG","MH","MK","ML",
    "MM","MN","MO","MP","MQ","MR","MS","MT","MU","MV",
    "MW","MX","MY","MZ","NA","NC","NE","NF","NG","NI",
    "NL","NO","NP","NR","NU","NZ","OM","PA","PE","PF",
    "PG","PH","PK","PL","PM","PN","PR","PS","PT","PW",
    "PY","QA","RE","RO","RU","RW","SA","SB","SC","SD",
    "SE","SG","SH","SI","SJ","SK","SL","SM","SN","SO",
    "SR","ST","SV","SY","SZ","TC","TD","TF","TG","TH",
    "TJ","TK","TM","TN","TO","TL","TR","TT","TV","TW",
    "TZ","UA","UG","UM","US","UY","UZ","VA","VC","VE",
    "VG","VI","VN","VU","WF","WS","YE","YT","RS","ZA",
    "ZM","ME","ZW","A1","A2","O1","AX","GG","IM","JE",
    "BL","MF", "BQ"
]
cc_idx = dict((cc.lower(), i) for i,cc in enumerate(GeoIP_country_code))
cc_idx[''] = cc_idx['--']
cc_idx['an'] = cc_idx['cw'] #netherlands antilles / curacao
cc_idx['uk'] = cc_idx['gb'] #uk / great britain
cc_idx['ss'] = cc_idx['sd'] #south sudan / sudan

def init_logger(opts):
    level = logging.INFO
    handler = logging.StreamHandler()
    #handler = logging.handlers.SysLogHandler(address='/dev/log')
    if opts.debug:
        level = logging.DEBUG
        handler = logging.StreamHandler()
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

def parse_args(argv):
    if argv is None:
        argv = sys.argv[1:]
    p = optparse.OptionParser()

    cmdlist = []
    for cmd, (f, usage) in sorted(cmds.iteritems()):
        cmdlist.append('%-8s\t%%prog %s' % (cmd, usage))
    cmdlist = '\n  '.join(cmdlist)

    p.usage = '%%prog [options] <cmd> <arg>+\n\nExamples:\n  %s' % cmdlist

    p.add_option('-d', '--debug', action='store_true',
            default=False, help="debug mode")
    p.add_option('-g', '--geoip', action='store_true',
            default=False, help='test with C GeoIP module')
    p.add_option('-w', '--write-dat', help='write filename.dat')
    p.add_option('-l', '--locations', help='city locations csv')
    opts, args = p.parse_args(argv)

    #sanity check
    if not args or args[0] not in cmds:
        p.error('missing command. choose from: %s' % ' '.join(sorted(cmds)))

    return opts, args


def test_dbs(opts, args):
    """test reference.dat and test.dat against a list of IPs and print any differences"""
    if opts.geoip:
        import GeoIP
        geo_open = GeoIP.open
        logging.debug('using GeoIP module')
    else:
        geo_open = pygeoip.GeoIP
        logging.debug('using pygeoip module')

    dbtype, ref_file, test_file = args[:3]
    gi_ref = geo_open(ref_file, pygeoip.MEMORY_CACHE)
    gi_tst = geo_open(test_file, pygeoip.MEMORY_CACHE)

    if dbtype in ('asn', 'org'):
        get_ref = gi_ref.org_by_addr
        get_tst = gi_tst.org_by_addr
        isequal = lambda lhs, rhs: lhs == rhs
    elif dbtype == 'city':
        get_ref = gi_ref.record_by_addr
        get_tst = gi_tst.record_by_addr
        def isequal(lhs, rhs):
            if lhs and rhs:
                #Python's float rounding makes these unpredictable,
                #so just stomp them to ints as a sanity check.
                for k in ('latitude', 'longitude'):
                    lhs[k] = int(lhs[k])
                    rhs[k] = int(rhs[k])
            return lhs == rhs

    ok = bad = 0
    for ip in fileinput.input(args[3:]):
        ip = ip.strip()
        ref = get_ref(ip)
        tst = get_tst(ip)
        if not isequal(ref, tst):
            print ip, ref, tst
            bad += 1
        else:
            ok += 1
    print 'ok:', ok, 'bad:', bad
test_dbs.usage = 'test [asn|city] reference.dat test.dat ips.txt'


def gen_csv(f):
    """peek at rows from a csv and start yielding when we get past the comments
    to a row that starts with an int (split at : to check IPv6)"""
    def startswith_int(row):
        try:
            int(row[0].split(':', 1)[0])
            return True
        except ValueError:
            return False

    cr = csv.reader(f)
    return itertools.dropwhile(lambda x: not startswith_int(x), cr)


def flatten_city(opts, args):
    """flatten MM blocks and locations CSVs into one file for easier editing"""
    id_loc = dict((row[0], row[1:]) for row in gen_csv(open(opts.locations)))
    cw = csv.writer(sys.stdout, lineterminator='\n')
    for row in gen_csv(fileinput.input(args)):
        row[-1:] = id_loc[row[-1]]
        cw.writerow(row)
flatten_city.usage = '-l GeoLiteCity-Location.csv flat GeoLiteCity-Blocks.csv > flatcity.csv'


class RadixTreeNode(object):
    __slots__ = ['segment', 'lhs', 'rhs']
    def __init__(self, segment):
        self.segment = segment
        self.lhs = None
        self.rhs = None


class RadixTree(object):
    def __init__(self, debug=False):
        self.debug = debug

        self.netcount = 0
        self.segments = [RadixTreeNode(0)]
        self.data_offsets = {}
        self.data_segments = []
        self.cur_offset = 1

    def __setitem__(self, net, data):
        self.netcount += 1
        inet = int(net)
        node = self.segments[0]
        for depth in range(self.seek_depth, self.seek_depth - (net.prefixlen-1), -1):
            if inet & (1 << depth):
                if not node.rhs:
                    node.rhs = RadixTreeNode(len(self.segments))
                    self.segments.append(node.rhs)
                node = node.rhs
            else:
                if not node.lhs:
                    node.lhs = RadixTreeNode(len(self.segments))
                    self.segments.append(node.lhs)
                node = node.lhs

        if not data in self.data_offsets:
            self.data_offsets[data] = self.cur_offset
            enc_data = self.encode(*data)
            self.data_segments.append(enc_data)
            self.cur_offset += (len(enc_data))

        if self.debug:
            #store net after data for easier debugging
            data = data, net

        if inet & (1 << self.seek_depth - (net.prefixlen-1)):
            node.rhs = data
        else:
            node.lhs = data

    def gen_nets(self, opts, args):
        raise NotImplementedError

    def load(self, opts, args):
        for nets, data in self.gen_nets(opts, args):
            for net in nets:
                self[net] = data

    def dump_node(self, node):
        if not node:
            #empty leaf
            return '--'
        elif isinstance(node, RadixTreeNode):
            #internal node
            return node.segment
        else:
            #data leaf
            data = node[0] if self.debug else node
            return '%d %s' % (len(self.segments) + self.data_offsets[data], node)

    def dump(self):
        for node in self.segments:
            print node.segment, [self.dump_node(node.lhs), self.dump_node(node.rhs)]

    def encode(self, *args):
        raise NotImplementedError

    def encode_rec(self, rec, reclen):
        """encode rec as 4-byte little-endian int, then truncate it to reclen"""
        assert(reclen <= 4)
        return struct.pack('<I', rec)[:reclen]

    def serialize_node(self, node):
        if not node:
            #empty leaf
            rec = len(self.segments)
        elif isinstance(node, RadixTreeNode):
            #internal node
            rec = node.segment
        else:
            #data leaf
            data = node[0] if self.debug else node
            rec = len(self.segments) + self.data_offsets[data]
        return self.encode_rec(rec, self.reclen)

    def serialize(self, f):
        if len(self.segments) >= 2 ** (8 * self.segreclen):
            logging.warning('too many segments for final segment record size!')

        for node in self.segments:
            f.write(self.serialize_node(node.lhs))
            f.write(self.serialize_node(node.rhs))

        f.write(chr(42)) #So long, and thanks for all the fish!
        f.write(''.join(self.data_segments))

        f.write('csv2dat.py') #.dat file comment - can be anything
        f.write(chr(0xFF) * 3)
        f.write(chr(self.edition))
        f.write(self.encode_rec(len(self.segments), self.segreclen))


class ASNRadixTree(RadixTree):
    usage = '-w mmasn.dat mmasn GeoIPASNum2.csv'
    cmd = 'mmasn'
    seek_depth = 31
    edition = pygeoip.const.ASNUM_EDITION
    reclen = pygeoip.const.SEGMENT_RECORD_LENGTH
    segreclen = pygeoip.const.STANDARD_RECORD_LENGTH

    def gen_nets(self, opts, args):
        for lo, hi, asn in gen_csv(fileinput.input(args)):
            lo, hi = ipaddr.IPAddress(int(lo)), ipaddr.IPAddress(int(hi))
            nets = ipaddr.summarize_address_range(lo, hi)
            yield nets, (asn,)

    def encode(self, data):
        return data + '\0'


class ASNv6RadixTree(ASNRadixTree):
    usage = '-w mmasn6.dat mmasn6 GeoIPASNum2v6.csv'
    cmd = 'mmasn6'
    seek_depth = 127
    edition = pygeoip.const.ASNUM_EDITION_V6
    reclen = pygeoip.const.SEGMENT_RECORD_LENGTH
    segreclen = pygeoip.const.STANDARD_RECORD_LENGTH

    def gen_nets(self, opts, args):
        for _, _, lo, hi, asn in gen_csv(fileinput.input(args)):
            lo, hi = ipaddr.IPAddress(int(lo)), ipaddr.IPAddress(int(hi))
            nets = ipaddr.summarize_address_range(lo, hi)
            yield nets, (asn,)


class CityRev1RadixTree(RadixTree):
    usage = '-w mmcity.dat [-l GeoLiteCity-Location.csv] mmcity GeoLiteCity-Blocks.csv'
    cmd = 'mmcity'
    seek_depth = 31
    edition = pygeoip.const.CITY_EDITION_REV1
    reclen = pygeoip.const.SEGMENT_RECORD_LENGTH
    segreclen = pygeoip.const.STANDARD_RECORD_LENGTH

    def gen_nets(self, opts, args):
        id_loc = None
        if opts.locations:
            id_loc = dict((row[0], row[1:]) for row in gen_csv(open(opts.locations)))

        for row in gen_csv(fileinput.input(args)):
            lo, hi = row[:2]
            loc = row[2:]
            if id_loc:
                loc = id_loc[loc[0]]
            lo, hi = ipaddr.IPAddress(int(lo)), ipaddr.IPAddress(int(hi))
            nets = ipaddr.summarize_address_range(lo, hi)
            yield nets, tuple(loc)

    def encode(self, country, region, city, postal_code, lat, lon, metro_code, area_code):
        def str2num(num, ntype):
            return ntype(num) if num else ntype(0)

        country = country.lower()
        lat, lon = round(str2num(lat, float), 4), round(str2num(lon, float), 4)
        metro_code, area_code = str2num(metro_code, int), str2num(area_code, int)

        buf = []
        try:
            buf.append(chr(cc_idx[country]))
        except KeyError:
            logging.warning("'%s': missing country. update GeoIP_country_code?", country)
            buf.append('--')
        buf.append('\0'.join((region, city, postal_code)))
        buf.append('\0')
        buf.append(self.encode_rec(int((lat + 180) * 10000), 3))
        buf.append(self.encode_rec(int((lon + 180) * 10000), 3))
        if (metro_code or area_code) and country == 'us':
            buf.append(self.encode_rec(metro_code * 1000 + area_code, 3))
        else:
            buf.append('\0\0\0')
        return ''.join(buf)


class CityRev1v6RadixTree(CityRev1RadixTree):
    usage = '-w mmcity6.dat mmcity6 GeoLiteCityv6.csv'
    cmd = 'mmcity6'
    seek_depth = 127
    edition = pygeoip.const.CITY_EDITION_REV1
    reclen = pygeoip.const.SEGMENT_RECORD_LENGTH
    segreclen = pygeoip.const.STANDARD_RECORD_LENGTH

    def gen_nets(self, opts, args):
        for row in gen_csv(fileinput.input(args)):
            lo, hi = row[2:4]
            lo, hi = ipaddr.IPAddress(int(lo)), ipaddr.IPAddress(int(hi))
            nets = ipaddr.summarize_address_range(lo, hi)
            #v6 postal_code is after lat/lon instead of before like v4
            country, region, city, lat, lon, postal_code, metro_code, area_code = row[4:]
            yield nets, (country, region, city, postal_code, lat, lon, metro_code, area_code)


def build_dat(RTree, opts, args):
    tstart = time.time()
    r = RTree(debug=opts.debug)

    r.load(opts, args)

    if opts.debug:
        r.dump()

    with open(opts.write_dat, 'wb') as f:
        r.serialize(f)

    tstop = time.time()
    print 'wrote %d-node trie with %d networks (%d distinct labels) in %d seconds' % (
            len(r.segments), r.netcount, len(r.data_offsets), tstop - tstart)


rtrees = [ASNRadixTree, ASNv6RadixTree, CityRev1RadixTree, CityRev1v6RadixTree]
cmds = dict((rtree.cmd, (partial(build_dat, rtree), rtree.usage)) for rtree in rtrees)
cmds['flat'] = (flatten_city, flatten_city.usage)
cmds['test'] = (test_dbs, test_dbs.usage)

def main(argv=None):
    global opts
    opts, args = parse_args(argv)
    init_logger(opts)
    logging.debug(opts)
    logging.debug(args)

    cmd = args.pop(0)
    cmd, usage = cmds[cmd]
    return cmd(opts, args)


if __name__ == '__main__':
    rval = main()
    logging.shutdown()
    sys.exit(rval)


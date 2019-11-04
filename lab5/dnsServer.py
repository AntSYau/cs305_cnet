import struct
import dns.resolver
import time


class DNSHeader:
    Struct = struct.Struct('!6H')

    def __init__(self):
        self.__dict__ = {
            field: None
            for field in ('ID', 'QR', 'OpCode', 'AA', 'TC', 'RD', 'RA', 'Z',
                          'RCode', 'QDCount', 'ANCount', 'NSCount', 'ARCount')}

    def parse_header(self, data):
        self.ID, misc, self.QDCount, self.ANcount, \
        self.NScount, self.NScount = DNSHeader.Struct.unpack_from(data)
        self.QR = (misc & 0x8000) != 0
        self.OpCode = (misc & 0x7800) >> 11
        self.AA = (misc & 0x0400) != 0
        self.TC = (misc & 0x200) != 0
        self.RD = (misc & 0x100) != 0
        self.RA = (misc & 0x80) != 0
        self.Z = (misc & 0x70) >> 4  # Never used
        self.RCode = misc & 0xF

    def __str__(self):
        return '<DNSHeader {}>'.format(str(self.__dict__))


class DNSServer:
    cache = {"www.sample.me": {"A": [["127.0.0.1", 5, time.time()]], "AAAA": [["::1", 5, time.time()]]}}
    upstream = "114.114.114.114"
    supported_type = ["A", "AAAA", "CNAME", "MX", "TXT", "NS"]

    def query(self, domain, type):
        if type not in self.supported_type:
            print("hey! make up your mind!")
            return []

        if domain in self.cache.keys():
            x = self.cache[domain]

            if type in x.keys():
                # todo: judge ttl
                return x[type]
            else:
                self.cache[domain][type] = []

        else:
            self.cache[domain] = {}

        A = dns.resolver.query(domain, type)

        cache = []
        for i in A:
            cache.append(i.to_text())
        cache[1] = 0  # todo: ttl ident

        if cache is []:
            print("server says: isuehuhdfkuaydgfakuyrf")
            return []

        self.cache[domain][type] = cache


x = DNSServer()
print(x.query("www.baidu.com", "A"))

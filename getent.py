from ctypes import CDLL, Structure, Union, cast, pointer, sizeof, byref, create_string_buffer
from ctypes import ARRAY, POINTER
from ctypes import c_void_p, c_uint, c_char_p, c_char, c_int, c_long, c_ulong, c_ubyte, c_ushort
from ctypes.util import find_library
from datetime import datetime
import socket
import struct
try:
    from collections import namedtuple
except ImportError:
    namedtuple = None


LIBC = CDLL(find_library("c"))
AF_INET = socket.AF_INET
AF_INET6 = socket.AF_INET6
INADDRSZ = 4
IN6ADDRSZ = 16

# Types
uint8_t = c_ubyte
uint16_t = c_ushort
uint32_t = c_uint
c_size_t = c_int
sa_family_t = c_ushort


class AliasStruct(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('members_len', c_size_t),
        ('members', POINTER(c_char_p)),
        ('local', c_int),
    ]


class InAddrStruct(Structure):
    # Taken from <netinet/in.h>
    _fields_ = [
        ('s_addr', uint32_t),
    ]


class InAddr6Union(Union):
    _fields_ = [
        ('u6_addr8', ARRAY(uint8_t, 16)),
        ('u6_addr16', ARRAY(uint16_t, 8)),
        ('u6_addr32', ARRAY(uint32_t, 4)),
    ]


class InAddr6Struct(Structure):
    # Taken from <netinet/in.h>
    _anonymous_ = ('in6_u',)
    _fields_ = [
        ('in6_u', InAddr6Union),
    ]


class HostStruct(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('aliases', POINTER(c_char_p)),
        ('addrtype', c_int),
        ('addr_list_len', c_int),
        ('addr_list', POINTER(c_void_p)),
    ]


class NetworkStruct(Structure):
    # Taken from <netdb.h>
    _fields_ = [
        ('name', c_char_p),             # official network name
        ('aliases', POINTER(c_char_p)), # alias list
        ('addrtype', c_int),            # net address type
        ('net', uint32_t),              # network number 
    ]


class GroupStruct(Structure):
    # Taken from <grp.h>
    _fields_ = [
        ("name", c_char_p),
        ("password", c_char_p),
        ("gid", c_int),
        ("members", POINTER(c_char_p)),
    ]


class PasswdStruct(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('password', c_char_p),
        ('uid', c_int),
        ('gid', c_int),
        ('gecos', c_char_p),
        ('dir', c_char_p),
        ('shell', c_char_p),
    ]


class ShadowStruct(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('password', c_char_p),
        ('change', c_long),
        ('min', c_long),
        ('max', c_long),
        ('warn', c_long),
        ('inact', c_long),
        ('expire', c_long),
        ('flag', c_ulong),
    ]


class StructMap(object):
    def __init__(self, p):
        self.p = p
        for attr in dir(self.p.contents):
            if attr.startswith('_'):
                continue
            elif not hasattr(self, attr):
                setattr(self, attr, getattr(self.p.contents, attr))

    def __dict__(self):
        return dict(iter(self))

    def __iter__(self):
        for attr in dir(self.p.contents):
            if attr.startswith('_'):
                continue
            else:
                yield (attr, getattr(self, attr))

    def _map(self, attr):
        i = 0
        obj = getattr(self.p.contents, attr)
        while obj[i]:
            yield obj[i]
            i += 1


def _resolve(addrtype, addr):
    if addrtype == AF_INET:
        p = cast(addr, POINTER(InAddrStruct))
        # Here we pack to little-endian to reverse back to
        # network byte order
        packed = struct.pack('<I', p.contents.s_addr)
        return socket.inet_ntop(addrtype, packed)
    elif addrtype == AF_INET6:
        p = cast(addr, POINTER(InAddr6Struct))
        packed = ''.join(map(lambda bit: struct.pack('<L', bit),
            p.contents.in6_u.u6_addr32))
        return socket.inet_ntop(addrtype, packed)


class Host(StructMap):
    def __init__(self, p):
        super(Host, self).__init__(p)
        self.aliases = list(self._map('aliases'))
        self.addresses = map(lambda addr: _resolve(self.addrtype, addr), 
            self._map('addr_list'))


class Network(StructMap):
    def __init__(self, p):
        super(Network, self).__init__(p)
        self.aliases = list(self._map('aliases'))


class Alias(StructMap):
    def __init__(self, p):
        super(Alias, self).__init__(p)
        self.members = list(self._map('members'))


class Group(StructMap):
    def __init__(self, p):
        super(Group, self).__init__(p)
        self.members = list(self._map('members'))


class Passwd(StructMap):
    pass


class Shadow(StructMap):
    def __init__(self, p):
        super(Shadow, self).__init__(p)
        self.change = datetime.fromtimestamp(p.contents.change)
        self.expire = datetime.fromtimestamp(p.contents.expire)


GENERATE = dict(
    alias = dict(
        base   = 'alias',
        struct = AliasStruct,
        mapper = Alias,
    ),
    host = dict(
        base   = 'host',
        struct = HostStruct,
        mapper = Host,
    ),
    network = dict(
        base   = 'net',
        struct = NetworkStruct,
        mapper = Network,
    ),
    group = dict(
        base   = 'gr',
        struct = GroupStruct,
        mapper = Group,
    ),
    passwd = dict(
        base   = 'pw',
        struct = PasswdStruct,
        mapper = Passwd,
    ),
    shadow = dict(
        base   = 'sp',
        struct = ShadowStruct,
        mapper = Shadow,
    ),
)

for name, info in GENERATE.iteritems():
    base = '%sent' % (info['base'],)
    # Map libc function calls
    globals()['set%s' % (base,)] = getattr(LIBC, 'set%s' % (base,))
    globals()['get%s' % (base,)] = getattr(LIBC, 'get%s' % (base,))
    globals()['get%s' % (base,)].restype = POINTER(info['struct'])
    globals()['end%s' % (base,)] = getattr(LIBC, 'end%s' % (base,))


inet_pton = LIBC.inet_pton
inet_pton.argtypes = (c_int, c_char_p, c_void_p)
inet_pton.restype = c_int
gethostbyaddr = LIBC.gethostbyaddr
gethostbyaddr.argtypes = (c_void_p, )
gethostbyaddr.restype = POINTER(HostStruct)
gethostbyname2 = LIBC.gethostbyname2
gethostbyname2.argtypes = (c_char_p, c_uint)
gethostbyname2.restype = POINTER(HostStruct)
getnetbyname = LIBC.getnetbyname
getnetbyname.argtypes = (c_char_p,)
getnetbyname.restype = POINTER(NetworkStruct)

class Keys(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, search=None):
        base = GENERATE[self.name]['base']
        maps = GENERATE[self.name]['mapper']
        func = globals()['get%sent' % (base,)]

        # Search generator, return all
        if search is None:
            globals()['set%sent' % (base,)]()
            while True:
                p = func()
                if p:
                    yield maps(p)
                else:
                    break
            globals()['end%sent' % (base,)]()


alias_keys = Keys('alias')
network_keys = Keys('network')
group_keys = Keys('group')
passwd_keys = Keys('passwd')
shadow_keys = Keys('shadow')

def host(search=None):
    # Iterate over all host entries
    if search is None:
        sethostent()
        p = True
        r = []
        while p:
            p = gethostent()
            if p:
                r.append(Host(p))
        endhostent()
        return r

    else:
        def lookup():
            addr = create_string_buffer(IN6ADDRSZ)

            # Test if input is an IPv6 address
            if inet_pton(AF_INET6, c_char_p(search), pointer(addr)) > 0:
                host = gethostbyaddr(addr, IN6ADDRSZ, AF_INET6)
                return host

            # Test if input is an IPv4 address
            if inet_pton(AF_INET, c_char_p(search), pointer(addr)) > 0:
                host = gethostbyaddr(addr, INADDRSZ, AF_INET)
                return host

            # Test if input is a hostname with an IPv6 address
            host = gethostbyname2(c_char_p(search), socket.AF_INET6)
            if host:
                return host

            # Test if input is a hostname with an IPv4 address
            host = gethostbyname2(c_char_p(search), socket.AF_INET)
            if host:
                return host

        host = lookup()
        if bool(host):
            return Host(host)

def network(search=None):
    if search is None:
        setnetent()
        p = True
        r = []
        while p:
            p = getnetent()
            if p: r.append(Network(p))
        endnetent()
        return r

    else:
        net = getnetbyname(c_char_p(search))
        if bool(net):
            return Network(net)

if __name__ == '__main__':
    print dict(host('127.0.0.1'))
    print dict(host('localhost'))

    for h in host():
        print dict(h)

    print dict(network('link-local') or {})

    for n in network_keys():
        print n.name, n.aliases

    for g in group_keys():
        print g.name, g.members, dict(g)

    for p in passwd_keys():
        print p.name, p.shell, p.dir, dict(p)

    for s in shadow_keys():
        print s.name, s.change, s.expire, dict(s)

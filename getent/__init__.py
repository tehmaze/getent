from datetime import datetime
import socket
import struct
from getent.constants import *
from getent.libc import *
from getent import headers


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
        p = cast(addr, POINTER(headers.InAddrStruct))
        # Here we pack to little-endian to reverse back to
        # network byte order
        packed = struct.pack('<I', p.contents.s_addr)
        return socket.inet_ntop(addrtype, packed)
    elif addrtype == AF_INET6:
        p = cast(addr, POINTER(headers.InAddr6Struct))
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

def alias(search=None):
    # Iterate over all alias entries
    if search is None:
        setaliasent()
        p = True
        r = []
        while p:
            p = getaliasent()
            if p:
                r.append(Alias(p))
        endaliasent()
        return r


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

def group(search=None):
    # Iterate over all group entries
    if search is None:
        setgrent()
        p = True
        r = []
        while p:
            p = getgrent()
            if p: r.append(Group(p))
        endgrent()
        return r

def passwd(search=None):
    # Iterate over all passwd entries
    if search is None:
        setpwent()
        p = True
        r = []
        while p:
            p = getpwent()
            if p: r.append(Passwd(p))
        endpwent()
        return r

def shadow(search=None):
    # Iterate over all shadow entries
    if search is None:
        setspent()
        p = True
        r = []
        while p:
            p = getspent()
            if p: r.append(Shadow(p))
        endspent()
        return r


if __name__ == '__main__':
    print dict(host('127.0.0.1'))
    print dict(host('localhost'))

    for h in host():
        print dict(h)

    print dict(network('link-local') or {})

    for n in network():
        print n.name, n.aliases

    for g in group():
        print g.name, g.members, dict(g)

    for p in passwd():
        print p.name, p.shell, p.dir, dict(p)

    for s in shadow():
        print s.name, s.change, s.expire, dict(s)

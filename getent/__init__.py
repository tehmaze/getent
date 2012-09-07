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


class Proto(StructMap):
    def __init__(self, p):
        super(Proto, self).__init__(p)
        self.aliases = list(self._map('aliases'))


class RPC(StructMap):
    def __init__(self, p):
        super(RPC, self).__init__(p)
        self.aliases = list(self._map('aliases'))


class Service(StructMap):
    def __init__(self, p):
        super(Service, self).__init__(p)
        self.aliases = list(self._map('aliases'))


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

def proto(search=None):
    if search is None:
        setprotoent()
        prt = True
        res = []
        while prt:
            prt = getprotoent()
            if prt:
                res.append(Proto(prt))
        endprotoent()
        return res

    else:
        search = str(search)
        if search.isdigit():
            prt = getprotobynumber(uid_t(long(search)))
        else:
            prt = getprotobyname(c_char_p(search))

        if bool(prt):
            return Proto(prt)

def rpc(search=None):
    if search is None:
        setrpcent()
        rpc = True
        res = []
        while rpc:
            rpc = getrpcent()
            if rpc:
                res.append(RPC(rpc))
        endrpcent()
        return res

    else:
        search = str(search)
        if search.isdigit():
            rpc = getrpcbynumber(uid_t(long(search)))
        else:
            rpc = getrpcbyname(c_char_p(search))

        if bool(rpc):
            return RPC(rpc)

def service(search=None, proto=None):
    '''
    Perform a service lookup.

    To lookup all services::

        >>> for item in service():
        ...

    To lookup one service by port number::

        >>> http = service(0, 'tcp')
        >>> print http.port
        80

    Or by service name::

        >>> smtp = service('smtp', 'tcp')
        >>> print smtp.port
        25

    Or by short notation::

        >>> snmp = service('udp/snmp')
        >>> print snmp.port
        161

    '''
    if search is None:
        setservent()
        srv = True
        res = []
        while srv:
            srv = getservent()
            if srv:
                res.append(Service(srv))
        endservent()
        return res

    else:
        search = str(search)
        if not proto and '/' in search:
            proto, search = search.split('/')
        if not proto in ['tcp', 'udp']:
            raise ValueError('Unsupported protocol "%s"' % (str(proto),))
        if search.isdigit():
            srv = getservbyport(uid_t(long(search)), c_char_p(proto))
        else:
            srv = getservbyname(c_char_p(search), c_char_p(proto))

        if bool(srv):
            return Service(srv)

def network(search=None):
    '''
    Perform a network lookup.

    To lookup all services::

        >>> for item in network():
        ...

    To lookup one network by name::

        >>> net = network('link-local')

    '''
    if search is None:
        setnetent()
        net = True
        res = []
        while net:
            net = getnetent()
            if net:
                res.append(Network(net))
        endnetent()
        return res

    else:
        net = getnetbyname(c_char_p(search))
        if bool(net):
            return Network(net)

def group(search=None):
    '''
    Perform a group lookup.

    To lookup all groups::

        >>> for item in group():
        ...

    To lookup one group by group id (gid)::

        >>> root = group(0)
        >>> print root.name
        'root'

    To lookup one group by name::

        >>> root = group('root')
        >>> print root.gid
        0

    '''
    # Iterate over all group entries
    if search is None:
        setgrent()
        grp = True
        res = []
        while grp:
            grp = getgrent()
            if grp:
                res.append(Group(grp))
        endgrent()
        return res

    else:
        search = str(search)
        if search.isdigit():
            grp = getgrgid(gid_t(long(search)))
        else:
            grp = getgrnam(c_char_p(search))

        if bool(grp):
            return Group(grp)

def passwd(search=None):
    '''
    Perform a passwd lookup.

    To lookup all passwd entries::

        >>> for item in passwd():
        ...

    To lookup one user by user id (uid)::

        >>> root = passwd(0)
        >>> print root.name
        'root'

    To lookup one user by name::

        >>> root = passwd('root')
        >>> print root.uid
        0

    '''
    # Iterate over all passwd entries
    if search is None:
        setpwent()
        pwd = True
        res = []
        while pwd:
            pwd = getpwent()
            if pwd:
                res.append(Passwd(pwd))
        endpwent()
        return res

    else:
        search = str(search)
        if search.isdigit():
            pwd = getpwuid(uid_t(long(search)))
        else:
            pwd = getpwnam(c_char_p(search))

        if bool(pwd):
            return Passwd(pwd)

def shadow(search=None):
    '''
    Perform a shadow lookup.

    To lookup all shadow entries::

        >>> for item in shadow():
        ...

    To lookup one user by name::

        >>> root = shadow('root') 
        >>> print root.warn # doctest: +SKIP
        99999

    '''
    # Iterate over all shadow entries
    if search is None:
        setspent()
        spe = True
        res = []
        while spe:
            spe = getspent()
            if spe:
                res.append(Shadow(spe))
        endspent()
        return res

    else:
        spe = getspnam(search)
        if bool(spe):
            return Shadow(spe)

if __name__ == '__main__':
    print dict(host('127.0.0.1'))
    print dict(host('localhost'))

    for h in host():
        print dict(h)

    print dict(network('link-local') or {})

    for p in proto():
        print p.name, p.aliases

    for r in rpc():
        print r.name, r.aliases

    for s in service():
        print s.name, s.port, s.proto

    for n in network():
        print n.name, n.aliases

    for g in group():
        print g.name, g.members, dict(g)

    for p in passwd():
        print p.name, p.shell, p.dir, dict(p)

    for s in shadow():
        print s.name, s.change, s.expire, dict(s)

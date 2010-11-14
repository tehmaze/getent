from getent.constants import *
from getent import headers
from ctypes.util import find_library

__all__ = ['GENERATE_MAP', 'libc', 'inet_pton', 'gethostbyaddr', 'gethostbyname2', 'getnetbyname']

# Libc object
libc = CDLL(find_library("c"))

GENERATE_MAP = dict(
    alias = headers.AliasStruct,
    host = headers.HostStruct,
    net = headers.NetworkStruct,
    gr = headers.GroupStruct,
    pw = headers.PasswordStruct,
    sp = headers.ShadowStruct,
)

# Map libc function calls
for name, struct in GENERATE_MAP.iteritems():
    base = '%sent' % (name,)
    globals()['set%s' % (base,)] = getattr(libc, 'set%s' % (base,))
    globals()['get%s' % (base,)] = getattr(libc, 'get%s' % (base,))
    globals()['get%s' % (base,)].restype = POINTER(struct)
    globals()['end%s' % (base,)] = getattr(libc, 'end%s' % (base,))
    __all__.append('set%s' % (base,))
    __all__.append('get%s' % (base,))
    __all__.append('end%s' % (base,))


inet_pton = libc.inet_pton
inet_pton.argtypes = (c_int, c_char_p, c_void_p)
inet_pton.restype = c_int
gethostbyaddr = libc.gethostbyaddr
gethostbyaddr.argtypes = (c_void_p, )
gethostbyaddr.restype = POINTER(headers.HostStruct)
gethostbyname2 = libc.gethostbyname2
gethostbyname2.argtypes = (c_char_p, c_uint)
gethostbyname2.restype = POINTER(headers.HostStruct)
getnetbyname = libc.getnetbyname
getnetbyname.argtypes = (c_char_p,)
getnetbyname.restype = POINTER(headers.NetworkStruct)

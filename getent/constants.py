from ctypes import CDLL, Structure, Union, cast, pointer, sizeof, byref, create_string_buffer
from ctypes import ARRAY, POINTER
from ctypes import c_void_p, c_uint, c_char_p, c_char, c_int, c_long, c_ulong, c_ubyte, c_ushort
import socket

# Socket
AF_INET = socket.AF_INET
AF_INET6 = socket.AF_INET6
INADDRSZ = 4
IN6ADDRSZ = 16

# Types
uint8_t = c_ubyte
uint16_t = c_ushort
uint32_t = c_uint
uid_t = c_uint
gid_t = c_uint
size_t = c_int
sa_family_t = c_ushort

#
#  GemUO
#
#  Copyright 2005-2020 Max Kellermann <max.kellermann@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 of the License.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#

import string, struct
from uo.error import ProtocolError

def decode_ustring(x):
    return x.decode('utf-16be', errors='replace')

def decode_ustring_list(x):
    result = []
    i = 0
    while i < len(x):
        l = struct.unpack('>H', x[i:i+2])[0]
        i += 2
        result.append(decode_ustring(x[i:i+l*2]))
        i += l * 2

    return result

packet_lengths = [
    0x0068, 0x0005, 0x0007, 0x0000, 0x0002, 0x0005, 0x0005, 0x0007, # 0x00
    0x000e, 0x0005, 0x0007, 0x0007, 0x0000, 0x0003, 0x0000, 0x003d, # 0x08
    0x00d7, 0x0000, 0x0000, 0x000a, 0x0006, 0x0009, 0x0001, 0x0000, # 0x10
    0x0000, 0x0000, 0x0000, 0x0025, 0x0000, 0x0005, 0x0004, 0x0008, # 0x18
    0x0013, 0x0008, 0x0003, 0x001a, 0x0007, 0x0014, 0x0005, 0x0002, # 0x20
    0x0005, 0x0001, 0x0005, 0x0002, 0x0002, 0x0011, 0x000f, 0x000a, # 0x28
    0x0005, 0x0001, 0x0002, 0x0002, 0x000a, 0x028d, 0x0000, 0x0008, # 0x30
    0x0007, 0x0009, 0x0000, 0x0000, 0x0000, 0x0002, 0x0025, 0x0000, # 0x38
    0x00c9, 0x0000, 0x0000, 0x0229, 0x02c9, 0x0005, 0x0000, 0x000b, # 0x40
    0x0049, 0x005d, 0x0005, 0x0009, 0x0000, 0x0000, 0x0006, 0x0002, # 0x48
    0x0000, 0x0000, 0x0000, 0x0002, 0x000c, 0x0001, 0x000b, 0x006e, # 0x50
    0x006a, 0x0000, 0x0000, 0x0004, 0x0002, 0x0049, 0x0000, 0x0031, # 0x58
    0x0005, 0x0009, 0x000f, 0x000d, 0x0001, 0x0004, 0x0000, 0x0015, # 0x60
    0x0000, 0x0000, 0x0003, 0x0009, 0x0013, 0x0003, 0x000e, 0x0000, # 0x68
    0x001c, 0x0000, 0x0005, 0x0002, 0x0000, 0x0023, 0x0010, 0x0011, # 0x70
    0x0000, 0x0009, 0x0000, 0x0002, 0x0000, 0x000d, 0x0002, 0x0000, # 0x78
    0x003e, 0x0000, 0x0002, 0x0027, 0x0045, 0x0002, 0x0000, 0x0000, # 0x80
    0x0042, 0x0000, 0x0000, 0x0000, 0x000b, 0x0000, 0x0000, 0x0000, # 0x88
    0x0013, 0x0041, 0x0000, 0x0063, 0x0000, 0x0009, 0x0000, 0x0002, # 0x90
    0x0000, 0x001a, 0x0000, 0x0102, 0x0135, 0x0033, 0x0000, 0x0000, # 0x98
    0x0003, 0x0009, 0x0009, 0x0009, 0x0095, 0x0000, 0x0000, 0x0004, # 0xA0
    0x0000, 0x0000, 0x0005, 0x0000, 0x0000, 0x0000, 0x0000, 0x000d, # 0xA8
    0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0040, 0x0009, 0x0000, # 0xB0
    0x0000, 0x0003, 0x0006, 0x0009, 0x0003, 0x0000, 0x0000, 0x0000, # 0xB8
    0x0024, 0x0000, 0x0000, 0x0000, 0x0006, 0x00cb, 0x0001, 0x0031, # 0xC0
    0x0002, 0x0006, 0x0006, 0x0007, 0x0000, 0x0001, 0x0000, 0x004e, # 0xC8
    0x0000, 0x0002, 0x0019, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, # 0xD0
    0x0000, 0x010C, 0xFFFF, 0xFFFF, 0x0009, 0x0000, 0xFFFF, 0x0000, # 0xD8
    0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, # 0xE0
    0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0x0015, # 0xE8
    0x0000, 0x0009, 0xFFFF, 0x001a, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, # 0xF0
    0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, # 0xF8
]

class PacketReader:
    def __init__(self, cmd, data):
        self.cmd = cmd
        self._data = data

    def __len__(self):
        return len(self._data)

    def data(self, length):
        if len(self._data) < length:
            raise ProtocolError("Packet is too short")
        x, self._data = self._data[:length], self._data[length:]
        return x

    def ulong(self):
        return struct.unpack('>Q', self.data(8))[0]

    def uint(self):
        return struct.unpack('>I', self.data(4))[0]

    def ushort(self):
        return struct.unpack('>H', self.data(2))[0]

    def byte(self):
        return struct.unpack('>B', self.data(1))[0]

    def boolean(self):
        return self.byte() != 0

    def fixstring(self, length):
        return self.data(length).replace(b'\0', b'').decode('utf-8', errors='replace')

    def cstring(self):
        i = self._data.index(b'\0')
        x, self._data = self._data[:i], self._data[i+1:]
        return x.decode('utf-8', errors='replace')

    def pstring(self):
        return self.fixstring(self.byte())

    def ucstring(self):
        x = ''
        while True:
            i = self.ushort()
            if i == 0:
                break
            x += chr(i)
        return x

    def ipv4(self):
        return '.'.join(map(str, struct.unpack('4B', self.data(4))))

class PacketWriter:
    def __init__(self, cmd):
        self._data = bytearray()
        self.byte(cmd)
        self._length = packet_lengths[cmd]
        if self._length == 0xffff:
            raise ProtocolError("Unsupported packet")

    def data(self, x):
        self._data += x

    def uint(self, x):
        self.data(struct.pack('>I', x))

    def ushort(self, x):
        assert x >= 0 and x < 65536
        self.data(struct.pack('>H', x))

    def sshort(self, x):
        assert x >= -32768 and x < 32768
        self.data(struct.pack('>h', x))

    def byte(self, x):
        assert x >= 0 and x < 256
        self.data(struct.pack('>B', x))

    def sbyte(self, x):
        assert x >= -128 and x < 128
        self.data(struct.pack('>b', x))

    def boolean(self, x):
        if x:
            self.byte(1)
        else:
            self.byte(0)

    def fixstring(self, x, length):
        x = x.encode('utf-8', errors='replace')
        if len(x) > length:
            raise ProtocolError("String is too long")
        self.data(x)
        self.data(b'\0' * (length - len(x)))

    def cstring(self, x):
        self.data(x.encode('utf-8', errors='replace'))
        self.byte(0)

    def ucstring(self, x):
        self.data(x.encode('utf-16be', errors='replace'))
        self.ushort(0)

    def finish(self):
        data = self._data
        if self._length == 0:
            if len(data) > 0xf000:
                raise ProtocolError("Packet too large")
            data[1:1] = struct.pack('>H', len(data) + 2)
        else:
            if len(data) != self._length:
                print(self._length, repr(data))
                raise ProtocolError("Invalid packet length")
        if isinstance(data, bytearray):
            return bytes(data)
        return data

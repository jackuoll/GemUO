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

# Loader for the UO client data files.

import os
import struct

FLAG_IMPASSABLE = 0x40
FLAG_SURFACE = 0x200

class TileData:
    def __init__(self, path):
        f = open(path, 'rb')

        # detect file format
        f.seek(36)
        x = f.read(20).rstrip(b'\0')
        f.seek(0)
        if x.find(b'\0') == -1:
            # old file format
            read_flags = lambda f: struct.unpack('<I', f.read(4))[0]
            item_count = 0x200
        else:
            # new file format (>= 7.0)
            read_flags = lambda f: struct.unpack('<Q', f.read(8))[0]
            item_count = 0x400

        self.land_flags = []
        for a in range(0x200):
            f.seek(4, 1)
            for b in range(0x20):
                self.land_flags.append(read_flags(f))
                f.seek(22, 1) # skip texture and name
        assert len(self.land_flags) == 0x4000

        self.item_flags = []
        for a in range(item_count):
            f.seek(4, 1)
            for b in range(0x20):
                self.item_flags.append(read_flags(f))
                f.seek(33, 1)
        assert len(self.item_flags) == item_count * 0x20

    def land_passable(self, id):
        assert id >= 0 and id < len(self.land_flags)
        return (self.land_flags[id] & FLAG_IMPASSABLE) == 0

    def item_passable(self, id):
        assert id >= 0 and id < len(self.item_flags)
        return (self.item_flags[id] & FLAG_IMPASSABLE) == 0

    def item_surface(self, id):
        assert id >= 0 and id < len(self.item_flags)
        return (self.item_flags[id] & FLAG_SURFACE) == 0

class LandBlock:
    def __init__(self, data):
        assert len(data) == 192
        self.data = data

    def get_id(self, x, y):
        assert x >= 0 and x < 8
        assert y >= 0 and y < 8

        i = (y * 8 + x) * 3
        return struct.unpack_from('<H', self.data, i)[0]

    def get_height(self, x, y):
        assert x >= 0 and x < 8
        assert y >= 0 and y < 8

        i = (y * 8 + x) * 3
        return ord(self.data[i + 2])

class LandLoader:
    def __init__(self, path, width, height):
        self.file = open(path, 'rb')
        self.width = width
        self.height = height

    def load_block(self, x, y):
        assert x >= 0 and x < self.width
        assert y >= 0 and y < self.height

        self.file.seek(((x * self.height) + y) * 196 + 4)
        return LandBlock(self.file.read(192))

class IndexLoader:
    def __init__(self, path, width, height):
        self.file = open(path, 'rb')
        self.width = width
        self.height = height

    def load_block(self, x, y):
        assert x >= 0 and x < self.width
        assert y >= 0 and y < self.height

        self.file.seek(((x * self.height) + y) * 12)
        data = self.file.read(8)
        offset, length = struct.unpack('<ii', data)
        if offset < 0 or length <= 0:
            return None, 0
        return offset, length

class Static:
    def __init__(self, id, x, y, z, hue=None):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.hue = hue

class StaticsList:
    def __init__(self, data):
        self.data = data
        self.passable = None # bit field, see _build_passable()
        self.surface = None

    def __iter__(self):
        i = 0
        while i < len(self.data):
            id, x, y, z, hue = struct.unpack_from('<HBBbH', self.data, i)
            yield id, x, y, z, hue
            i += 7

    def iter_at(self, x, y):
        for id, ix, iy, z, hue in self:
            if ix == x and iy == y:
                yield id, z, hue

    def _build_passable(self, tile_data):
        # each of the 64 bits tells whether the position is passable
        passable = 0xffffffffffffffff
        for id, x, y, z, hue in self:
            if not tile_data.item_passable(id):
                bit = x * 8 + y
                passable &= ~(1 << bit)
        self.passable = passable

    def is_passable(self, tile_data, x, y, z):
        if self.passable is None:
            self._build_passable(tile_data)
        bit = x * 8 + y
        return (self.passable & (1 << bit)) != 0

    def _build_surface(self, tile_data):
        # each of the 64 bits tells whether the position is surface
        surface = 0
        for id, x, y, z, hue in self:
            if not tile_data.item_surface(id):
                bit = x * 8 + y
                surface |= 1 << bit
        self.surface = surface

    def is_surface(self, tile_data, x, y):
        if self.surface is None:
            self._build_surface(tile_data)
        bit = x * 8 + y
        return (self.surface & (1 << bit)) != 0

class StaticsLoader:
    def __init__(self, path):
        self.file = open(path, 'rb')

    def load_block(self, offset, length):
        self.file.seek(offset)
        return StaticsList(self.file.read(length))

class StaticsGlue:
    def __init__(self, index, static):
        self.index = index
        self.static = static

    def load_block(self, x, y):
        offset, length = self.index.load_block(x, y)
        if length == 0: return None
        return self.static.load_block(offset, length)

class MapGlue:
    def __init__(self, tile_data, map_path, index_path, statics_path, width, height):
        self.tile_data = tile_data
        self.land = LandLoader(map_path, width, height)
        self.statics = StaticsGlue(IndexLoader(index_path, width, height),
                                   StaticsLoader(statics_path))

    def land_tile_id(self, x, y):
        block = self.land.load_block(x // 8, y // 8)
        return block.get_id(x % 8, y % 8)

    def land_tile_flags(self, x, y):
        return self.tile_data.land_flags[self.land_tile_id(x, y)]

    def land_tile_height(self, x, y):
        block = self.land.load_block(x // 8, y // 8)
        return block.get_height(x % 8, y % 8)

    def statics_at(self, x, y):
        block = self.statics.load_block(x // 8, y // 8)
        if block is None: return iter(())
        return block.iter_at(x % 8, y %8)

    def is_passable(self, x, y, z):
        statics = self.statics.load_block(x // 8, y // 8)
        if statics is not None and not statics.is_passable(self.tile_data, x % 8, y % 8, z):
            return False

        # even if land is impassable, there may be statics that build
        # a "surface" to walk on
        block = self.land.load_block(x // 8, y // 8)
        if not self.tile_data.land_passable(block.get_id(x % 8, y % 8)) and \
            (statics is None or not statics.is_surface(self.tile_data, x % 8, y % 8)):
            return False

        #bz = block.get_height(x % 8, y % 8)
        #if bz > z: return False

        return True

    def surface_at(self, x, y):
        for id, z, hue in self.statics_at(x, y):
            if self.tile_data.item_surface(id):
                return Static(id, x, y, z, hue)

        return None

    def flush_cache(self):
        # not implemented in this base class
        pass

class BlockCache:
    def __init__(self, loader):
        self._loader = loader
        self._cache = dict()

    def load_block(self, x, y):
        i = x * 65536 + y
        try:
            return self._cache[i]
        except KeyError:
            b = self._loader.load_block(x, y)
            self._cache[i] = b
            return b

class CachedMapGlue(MapGlue):
    def __init__(self, *args, **keywords):
        MapGlue.__init__(self, *args, **keywords)
        self.land = BlockCache(self.land)
        self.statics = BlockCache(self.statics)

class TileCache:
    def __init__(self, path):
        self._path = path
        self._tile_data = TileData(os.path.join(self._path, 'tiledata.mul'))
        self._maps = {}

    def get_map(self, i):
        if i in self._maps:
            return self._maps[i]
        m = CachedMapGlue(self._tile_data,
                          os.path.join(self._path, 'map%u.mul' % i),
                          os.path.join(self._path, 'staidx%u.mul' % i),
                          os.path.join(self._path, 'statics%u.mul' % i),
                          768, 512)
        self._maps[i] = m
        return m

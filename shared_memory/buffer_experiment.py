import mmap
import struct


class SharedMemoryBuffer:
    _MAGIC = 0x4348524F4E4F5331
    _HEADER_FORMAT = "<QQQ"
    _COUNTERS_FORMAT = "<QQ"

    def __init__(
        self,
        size=2097152,
        tag_name="Local\\ChronosMatchSharedBufferV3"
    ):
        self.size = size
        self.tag_name = tag_name
        self.struct_format = "Qdic"
        self.record_size = struct.calcsize(self.struct_format)
        self.header_size = struct.calcsize(self._HEADER_FORMAT)
        self.capacity = (self.size - self.header_size) // self.record_size

        if self.capacity < 1:
            raise ValueError("Shared memory size must fit at least one order")

        self.mm = mmap.mmap(
            -1,
            self.size,
            tagname=self.tag_name,
            access=mmap.ACCESS_WRITE
        )

        if len(self.mm[:self.header_size]) != self.header_size:
            self.mm.close()
            raise RuntimeError("Unable to read shared memory header")

        magic = struct.unpack("<Q", self.mm[:8])[0]
        if magic != self._MAGIC:
            self.reset_buffer()

    def reset_buffer(self):
        self.mm[:self.header_size] = struct.pack(
            self._HEADER_FORMAT,
            self._MAGIC,
            0,
            0
        )
        self.mm.flush()

    def write_order(
        self,
        order_id: int,
        price: float,
        qty: int,
        side: bytes
    ):
        if side not in (b"B", b"S"):
            raise ValueError("Side must be b'B' or b'S'")

        packed_bytes = struct.pack(
            self.struct_format,
            order_id,
            price,
            qty,
            side
        )

        write_seq, read_seq = struct.unpack(
            self._COUNTERS_FORMAT,
            self.mm[8:self.header_size]
        )
        if write_seq < read_seq or write_seq - read_seq > self.capacity:
            raise RuntimeError("Shared memory queue counters are inconsistent")
        if write_seq - read_seq == self.capacity:
            raise BufferError("Shared memory order queue is full")

        slot = write_seq % self.capacity
        start = self.header_size + slot * self.record_size
        self.mm[start:start + self.record_size] = packed_bytes
        self.mm[8:16] = struct.pack("<Q", write_seq + 1)

    def read_next_order(self):
        write_seq, read_seq = struct.unpack(
            self._COUNTERS_FORMAT,
            self.mm[8:self.header_size]
        )
        if write_seq < read_seq or write_seq - read_seq > self.capacity:
            raise RuntimeError("Shared memory queue counters are inconsistent")
        if write_seq == read_seq:
            return None

        slot = read_seq % self.capacity
        start = self.header_size + slot * self.record_size
        raw_bytes = self.mm[start:start + self.record_size]
        order = struct.unpack(self.struct_format, raw_bytes)
        self.mm[16:24] = struct.pack("<Q", read_seq + 1)
        return order

    def read_latest_order(self):
        return self.read_next_order()

    def close(self):
        self.mm.close()

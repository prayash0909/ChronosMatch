from multiprocessing import shared_memory
import struct


class SharedMemoryBufferExperiment:
    _MAGIC = 0x4348524F4E4F5331
    _HEADER_FORMAT = "<QQQ"
    _COUNTERS_FORMAT = "<QQ"

    def __init__(self, name=None, size=2097152, create=True):
        self.size = size
        self.struct_format = "Qdic"
        self.record_size = struct.calcsize(self.struct_format)
        self.header_size = struct.calcsize(self._HEADER_FORMAT)
        self.capacity = (size - self.header_size) // self.record_size
        self.owner = create

        if self.capacity < 1:
            raise ValueError("Shared memory size is too small")

        if create:
            self.shm = shared_memory.SharedMemory(
                create=True, size=size, name=name
            )
            self.name = self.shm.name
            self.reset_buffer()
        else:
            if not name:
                raise ValueError("A shared memory name is required")
            self.shm = shared_memory.SharedMemory(
                name=name, create=False
            )
            self.name = self.shm.name

            if self.shm.size < size:
                self.shm.close()
                raise ValueError("Existing shared memory is too small")

            magic = struct.unpack_from("<Q", self.shm.buf, 0)[0]
            if magic != self._MAGIC:
                self.shm.close()
                raise RuntimeError("Invalid shared memory header")

    def reset_buffer(self):
        struct.pack_into(
            self._HEADER_FORMAT,
            self.shm.buf,
            0,
            self._MAGIC,
            0,
            0
        )

    def write_order(self, order_id, price, qty, side):
        if side not in (b"B", b"S"):
            raise ValueError("Side must be b'B' or b'S'")

        packed = struct.pack(
            self.struct_format, order_id, price, qty, side
        )

        write_seq, read_seq = struct.unpack_from(
            self._COUNTERS_FORMAT, self.shm.buf, 8
        )

        if write_seq < read_seq or write_seq - read_seq > self.capacity:
            raise RuntimeError("Shared memory queue counters are inconsistent")

        if write_seq - read_seq == self.capacity:
            raise BufferError("Shared memory order queue is full")

        slot = write_seq % self.capacity
        start = self.header_size + slot * self.record_size
        self.shm.buf[start:start + self.record_size] = packed

        struct.pack_into("<Q", self.shm.buf, 8, write_seq + 1)

    def read_next_order(self):
        write_seq, read_seq = struct.unpack_from(
            self._COUNTERS_FORMAT, self.shm.buf, 8
        )

        if write_seq < read_seq or write_seq - read_seq > self.capacity:
            raise RuntimeError("Shared memory queue counters are inconsistent")

        if write_seq == read_seq:
            return None

        slot = read_seq % self.capacity
        start = self.header_size + slot * self.record_size
        raw = bytes(self.shm.buf[start:start + self.record_size])
        order = struct.unpack(self.struct_format, raw)

        struct.pack_into("<Q", self.shm.buf, 16, read_seq + 1)
        return order

    def close(self, unlink=False):
        self.shm.close()
        if unlink and self.owner:
            self.shm.unlink()

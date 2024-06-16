class ByteFIFO:
    """ byte FIFO buffer """

    def __init__(self):
        self._buf = bytearray()

    def put(self, data):
        self._buf.extend(data)

    def get(self, size):
        data = self._buf[:size]
        # The fast delete syntax
        self._buf[:size] = b''
        return bytes(data)

    def peek(self, size):
        return bytes(self._buf[:size])

    def __len__(self):
        return len(self._buf)

from . import vdevs


class FileDev(vdevs.VDev):
    def __init__(self, path, label=None, txg=None):
        self.f = open(path, 'r+b')
        super(FileDev, self).__init__(label, txg)

    def read(self, offset, size):
        self.seek(*offset)
        return self.f.read(size)

    def write(self, offset, data):
        self.seek(*offset)
        return self.f.write(data)

    def flush(self):
        return self.f.flush()

    def seek(self, offset, whence):
        return self.f.seek(offset, whence)

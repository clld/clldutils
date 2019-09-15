import io
import zipfile


class ZipArchive(zipfile.ZipFile):

    _init_defaults = {
        'compression': zipfile.ZIP_DEFLATED,
        'allowZip64': True,
    }

    def __init__(self, fname, mode='r', **kwargs):
        for k, v in self._init_defaults.items():
            kwargs.setdefault(k, v)
        super(ZipArchive, self).__init__(str(fname), mode=mode, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_text(self, name, encoding='utf-8-sig'):
        if name in self.namelist():
            return io.TextIOWrapper(self.open(name), encoding=encoding).read()

    def write_text(self, text, name, _encoding='utf-8'):
        if not isinstance(text, bytes):
            text = text.encode(_encoding)
        self.writestr(name, text)

import tablib


class Report(object):

    def __init__(self, data, headers=None):
        if headers:
            self.headers = headers
        else:
            self.headers = ('repo','hash', 'type', 'potential', 'lines')
        self.tdata = tablib.Dataset(*data, headers=self.headers)

    def toHtml(self):
        with open('harpocrates.html', 'w') as f:
            f.write(self.tdata.html)

    def toJson(self, toFile=False):
        if toFile:
            with open('harpocrates.json', 'w') as f:
                f.write(self.tdata.json)
        return self.tdata.json

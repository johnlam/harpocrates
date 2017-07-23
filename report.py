import tablib


class Report(object):

    def __init__(self, reponame, data, headers=None):
        self.reponame = reponame
        if headers:
            self.headers = headers
        else:
            self.headers = ('hash', 'type', 'potential')
        self.tdata = tablib.Dataset(*data, headers=self.headers)

    def toHtml(self):
        with open(self.reponame + '.html', 'wb') as f:
            f.write(self.tdata.html)

    def toJson(self, toFile=False):
        if toFile:
            with open(self.reponame + '.json', 'wb') as f:
                f.write(self.tdata.json)
        return self.tdata.json

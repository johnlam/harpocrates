import re
from git import Repo
import requests
import tempfile
import base64
from leak import Leaks, Leak
import time
from report import Report


class Harpocrates(object):
    def __init__(self, regex=None):
        if not regex:
            self.regexes = {
                "Credit Card":
                '(1800|2131|30[0-5]\d|3[4-7]\d{2}|4\d{3}|5[0-5]\d{2}|6011|6[2357]'
                '\d{2})[-]?(\d{4}[- ]?\d{4}[- ]?\d{4}|\d{6}[- ]?\d{5})',
                "United Kingdom Phone Number": '(?:(?:\(?(?:0(?:0|11)\)?[\s-]?\(?|'
                    '\+)44\)?[\s-]?(?:\(?0\)?[\s-]?)?)|(?:\(?0))(?:(?:\d{5}\)'
                    '?[\s-]?\d{4,5})|(?:\d{4}\)?[\s-]?(?:\d{5}|\d{3}[\s-]?\d'
                    '{3}))|(?:\d{3}\)?[\s-]?\d{3}[\s-]?\d{3,4})|(?:\d{2}\)?['
                    '\s-]?\d{4}[\s-]?\d{4}))(?:[\s-]?(?:x|ext\.?|\#)\d{3,4})?',
                "AWS ID": 'AKIA[0-9A-Z]{16}',
                "AWS Secret Precise": '(?<=(\'|\"| |\n))[A-Za-z0-9/+=]{40}'
                    '(?![a-zA-Z0-9])',
                "AWS Secret": '[A-Za-z0-9/+=]{40}',
                "Priv Keys": 'BEGIN RSA PRIVATE KEY',
                "United Kingdom National Insurance Number":
                '(?!BG)(?!GB)(?!NK)(?!KN)(?!TN)(?!NT)(?!ZZ)(?:[A-CEGHJ-PR-TW-Z][A'
                    '-CEGHJ-NPR-TW-Z])(?:\s*\d\s*){6}([A-D]|\s)',
                "Email": '[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}'
            }
        self.org_repos = {}

    @staticmethod
    def luhn_checksum(card_number):
        def digits_of(n):
            return [int(d) for d in str(n) if d.isdigit()]
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = 0
        checksum += sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10

    @staticmethod
    def is_luhn_valid(card_number):
        return Harpocrates.luhn_checksum(card_number) == 0

    def find_strings(self, git_url):
        self.results = Leaks()
        project_path = tempfile.mkdtemp()
        Repo.clone_from(git_url, project_path)
        repo = Repo(project_path)
        already_searched = set()

        for remote_branch in repo.remotes.origin.fetch():
            branch_name = str(remote_branch).split('/')[1]
            try:
                repo.git.checkout(remote_branch, b=branch_name)
            except:
                pass
            prev_commit = None
            for curr_commit in repo.iter_commits():
                if not prev_commit:
                    pass
                else:
                    # avoid searching the same diffs
                    hashes = str(prev_commit) + str(curr_commit)
                    if hashes in already_searched:
                        prev_commit = curr_commit
                        continue
                    already_searched.add(hashes)
                    diff = prev_commit.diff(curr_commit, create_patch=True)
                    for blob in diff:
                        printableDiff = blob.diff.decode('utf-8',
                                                         errors='replace')
                        if printableDiff.startswith("Binary files"):
                            continue
                        stringsFound = []
                        lines = blob.diff.decode('utf-8', errors='replace')
                        for k, v in self.regexes.iteritems():
                            if re.search(v, lines):
                                potential = re.search(v, lines).group(0)
                                if k in self.results and potential in self.results[k]:
                                    continue
                                if len(potential) * potential[0] == potential:
                                    continue
                                elif k.startswith('Credit Card'):
                                    if Harpocrates.is_luhn_valid(potential):
                                        self.results[k].add(
                                            Leak(curr_commit, potential))
                                elif k.startswith('AWS Secret'):
                                    try:
                                        base64.b64decode(potential)
                                        self.results[k].add(
                                            Leak(curr_commit, potential))
                                    except TypeError as e:
                                        continue
                                else:
                                    self.results[k].add(Leak(curr_commit,
                                                             potential))
                prev_commit = curr_commit

        return self.results

    def get_org_repos(self, orgname,sleep_time=2):
        cur_page, last_page = 1, 1
        url = 'https://api.github.com/orgs/' + orgname + '/repos?page='
        while cur_page <= last_page:
            print url
            response = requests.get(url + str(cur_page))
            print response.url
            print cur_page
            json = response.json()
            pat = '/repos\?page=(\d+)'
            p = re.compile(pat)
            page_info = p.findall(response.headers['Link'])
            print response.headers['Link']
            print page_info
            cur_page = int(page_info[0])
            last_page = int(page_info[1])
            for item in json:
                print response.headers['X-RateLimit-Remaining']
                if item['private'] == False:
                    print('searching ' + item["html_url"])
                    reponame = item["html_url"].split('/')[-1]
                    self.org_repos[reponame] = find_strings(item["html_url"])

            time.sleep(sleep_time)

    def get_report(self, reponame, data, out, headers):
        transformdata = []
        for k,items in data.iteritems():
            for item in items:
                transformdata.append((str(item),k,item.potential))

        r = Report(reponame, transformdata, headers)
        data = []
        if out == 'html':
            r.toHtml()
        elif out == 'jsonfile':
            r.toJson(toFile=True)
        elif out == 'json':
            return r.toJson()

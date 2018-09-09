import base64
import re
import tempfile
import time

import requests
from git import Repo
from truffleHogRegexes.regexChecks import regexes as truffleregex

from leak import Leak, Leaks
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
                "United Kingdom National Insurance Number":
                '(?!BG)(?!GB)(?!NK)(?!KN)(?!TN)(?!NT)(?!ZZ)(?:[A-CEGHJ-PR-TW-Z][A'
                    '-CEGHJ-NPR-TW-Z])(?:\s*\d\s*){6}([A-D]|\s)',
                "Email": '[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}',
                **truffleregex
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

    def get_repo(self, git_url):
        self.results = Leaks()
        project_path = tempfile.mkdtemp()
        Repo.clone_from(git_url, project_path)
        reponame = '/'.join(git_url.split('/')[-2:])
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
                        lines = blob.diff.decode('utf-8', errors='replace')
                        for k, v in self.regexes.items():
                            if re.search(v, lines):
                                potential = re.search(v, lines).group(0)
                                if k in self.results and potential in self.results[k]:
                                    continue
                                if len(potential) * potential[0] == potential:
                                    continue
                                elif k.startswith('Credit Card'):
                                    if Harpocrates.is_luhn_valid(potential):
                                        self.results[k].add(
                                            Leak(reponame, curr_commit, potential,
                                                 lines))
                                else:
                                    self.results[k].add(Leak(reponame,
                                                             curr_commit,
                                                             potential,
                                                             lines))
                prev_commit = curr_commit

        return self.results

    def get_org_repos(self, orgname, sleep_time=2):
        cur_page, last_page = 1, 1
        url = 'https://api.github.com/orgs/{}/repos?page=&per_page=100'.format(orgname)
        nextre = re.compile('/repos\?page=(\d+)>; rel="next"')
        lastre = re.compile('/repos\?page=(\d+)>; rel="last"')
        while cur_page <= last_page:
            response = requests.get(url + str(cur_page))
           
            if 'Link' in response.headers:
                cur_page = int(nextre.findall(response.headers['Link'])[0])
                last_page = int(lastre.findall(response.headers['Link'])[0])
            else:
                cur_page = last_page
            for item in response.json():
                print(response.headers['X-RateLimit-Remaining'])
                if item['private'] == False:
                    print('searching ' + item["html_url"])
                    reponame = item["html_url"].split('/')[-1]
                    self.org_repos[reponame] = self.get_repo(
                        item["html_url"])

            time.sleep(sleep_time)

    def get_report(self, out):
        transformdata = []
        for k, items in self.results.items():
            for item in items:
                transformdata.append(
                    (str(item), k, item.potential, item.lines))

        r = Report(transformdata)
        if out == 'html':
            r.toHtml()
        elif out == 'jsonfile':
            r.toJson(toFile=True)
        elif out == 'json':
            return r.toJson()

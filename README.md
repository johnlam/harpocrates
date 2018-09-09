# Harpocrates

Scan a git repo's history or a whole github org to match any potential
personal data or secrets.

The matches are made through regular expressions, therefore
there is always a very good change that some of the results
will contain false positives.

The regexes currently include
 * AWS Keys
 * Credit Cards
 * Private keys
 * Emails
 * UK National Insurance Number
 * UK Phone Numbers

Heavily based on [https://github.com/dxa4481/truffleHog](https://github.com/dxa4481/truffleHog)
(It will clone the repo(s) in your `/tmp`)
Harpocrates now uses truffleHog's regexes

## Install
```python
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

## Examples

Scan a repo

```python

from harpocrates import Harpocrates
h = Harpocrates()
repo = h.get_repo('https://github.com/foo/bar')

```
Scan a github org

```python
repo = h.get_org_repos('google')
```

You can provide your own regex as a dictionary

```python
myregex = {'Belgium ID Number':'[0-9]{2}\.?[0-9]{2}\.?[0-9]{2}-[0-9]{3}\.?[0-9]{2}'}
h = Harpocrates(regex=myregex)
```

## Reporting
Harpocrates uses [tablib](https://github.com/kennethreitz/tablib)

Get Json or Html
```python
res = c.get_report('json')
res = c.get_report('html')
```

## TODO
 - [ ] Package and Publish to PyPI
 - [ ] Make reporting better
 - [ ] Clone private repos

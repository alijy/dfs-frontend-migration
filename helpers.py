import re
import bs4


frontendUrl = '/Users/ali/code/hmrcdev/pool/dfs-frontend'
digitalUrl  = '/Users/ali/code/hmrcdev/pool/dfs-digital-forms-frontend'
templateUrl = '/Users/ali/code/hmrcdev/pool/dfs-template-renderer'


def sanitise(message_list):
  result = []
  cleaner = re.compile('<.*?>')
  for m in message_list:
    clean_text = re.sub(cleaner, '', m).strip("\\").strip()
    if clean_text != "":
      result.append(clean_text)
  return result


def get_data(d):
  if isinstance(d, bs4.element.NavigableString):
    yield d
  if d.name == 'a':
    yield d['href']
  yield from [i for b in getattr(d, 'contents', []) for i in get_data(b)]


def messageParser(message):
  return list(get_data(bs4.BeautifulSoup(message, 'html.parser')))


def isUrl(s):
  return s.startswith('/') or s.startswith('http') or s.startswith('www.')


# def refactoredDict(d):
#   refactoredList = []
#   tempDict = {}
#   for k, v in d.items():
#     tempDict[k] = v
#     if v.endswith('.'):
#       refactoredList.append(tempDict)
#       tempDict = {}
#   return refactoredList


def getLineNumber(fileUrl, lookup):
  lineNum = 0
  with open(fileUrl) as f:
    for num, line in enumerate(f, 1):
      if lookup in line:
        lineNum = num
  return lineNum


s = """page.guide.list.CBOptIn=<li>you''re the Child Benefit Claimant</li>\
  <li>you or your partner are affected by the High Income Child Benefit Charge</li>
"""
print(bs4.BeautifulSoup(s, 'html.parser'))
print([messageParser(str(item)) for item in bs4.BeautifulSoup(s, 'html.parser')])
print('-------------------------------------')
for i in bs4.BeautifulSoup(s, 'html.parser'):
  print(i)
print('-------------------------------------')
for i in bs4.BeautifulSoup(s, 'html.parser').findAll(lambda tag: tag.string.strip() is not None):
  print(i)


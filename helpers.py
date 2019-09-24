import re
import bs4
from lxml import html

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


def get_nested_list(formId, startFrom, size):
  s = f"@nestedList(params, \"{formId}\", Seq(\"guide.{startFrom:02d}\""
  for i in range(1, size):
    s += f", \"guide.{(startFrom + i):02d}\""
  s += "))"
  return s


def get_message_with_affinity(formId, num):
  return f"@MessagesUtils.getMessagesWithAffinity(\"guide.{num:02d}\", \"{formId}\", {{params(\"langLocaleCode\")}}.toString, {{params(\"affinityGroup\")}}.toString)"





# s = """page.guide.list.CBOptIn=<li>you''re the Child Benefit Claimant</li>\
#   <li>you or your partner are affected by the High Income Child Benefit Charge</li>
# """
s = """page.guide.extraInfo.CBOptIn=<p>You can also use this form to restart your Child Benefit payments if:<ul class="list-bullet">\
<li>you''re the Child Benefit Claimant</li>\
<li>you still <a href="/qualigy/for/benefit">qualify for Child Benefit</a></li>\
<li>you previously stopped your payments because of the High Income Child Benefit Tax Charge</li>\
</ul></p>\
"""
# print(bs4.BeautifulSoup(s, 'html.parser'))
# print([messageParser(str(item)) for item in bs4.BeautifulSoup(s, 'html.parser')])
# print('-------------------------------------')
# for i in bs4.BeautifulSoup(s, 'html.parser'):
#   print(type(i))
#   a = bs4.element.Tag
# print('-------------------------------------')
# for i in bs4.BeautifulSoup(s, 'html.parser').findAll(lambda tag: tag.string.strip() is not None):
#   print(i)
# for i in bs4.BeautifulSoup(s, 'html.parser'):
#   print(bs4.BeautifulSoup(i, 'html.parser'))

# print('=-----------------------------------=')
# xs = s.split("\n")
# html = ''
# for tag in xs:
#     if "<p" in tag and "</p" in tag:
#         soup = bs4.BeautifulSoup(tag, 'html.parser')
#         html = "{}\n{}".format(html, "[{}]".format(soup.text))
#     elif "<p" in tag:
#         html = "{}\n{}".format(html, "<ul>\n<li>{}</li>".format(tag[tag.find(">") + 1:]))
#     elif "</p" in tag:
#         html = "{}\n{}".format(html, "</ul>")
#
# print(html)


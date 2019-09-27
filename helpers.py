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


def index_of_urls(aList):
  return [i for i in range(len(aList)) if isUrl(aList[i])]


def get_link_template(aList, id, startAt, idx):
  if len(idx) == 1:
    return startAt + len(aList) - 1, get_generic_link(aList, id, startAt, idx[0])
  else:
    c = startAt
    s = ''
    s += f"\n\n<p>"
    urlIndex = -99
    for i, item in enumerate(aList):
      if isUrl(item):
        urlIndex = i
        s += f" <a href=\"{item}\">"
      else:
        s += f"{get_message_with_affinity(id, c)}"
        c += 1
        if i == urlIndex + 1:
          s += "</a>"
          urlIndex = -99
    s += "</p>"
    return c, s


def get_partial_template(formId, count, key, value):
  s = ''
  if key == 'beforeStart':
    s += f"\n\n@baseGenericGuidePageBody(params, \"{formId}\")"
    # print(f"\n\n@baseGenericGuidePageBody(params, \"{formId}\")")
  for item in value[1:]:
    split_lists = get_split_lists(item)
    # print(f"item => {item}")
    # print(f"split_lists => {split_lists}")
    for i in split_lists:
      # print(f"i => {i}")
      if not i: # empty list
        pass
      elif len(i) == 1: # contains a single paragraph
        s += f"\n\n<p>{get_message_with_affinity(formId, count)}</p>"
        count += 1
      elif i[0].endswith(':'):  # contains a list
        s += f"\n\n<p>{get_message_with_affinity(formId, count)}</p>"
        count += 1
        s += f"\n\n{get_nested_list(formId, count, len(i) - 1)}"
        count += len(i) - 1
      elif index_of_urls(i): # contains a link
        count, t = get_link_template(i, formId, count, index_of_urls(i))
        s += f"\n\n{t}"
      else:
        s += f"\n\n!!!!!!! This is an UNHANDLED variation !!!!!!!"
  return count, s


def get_line_number(fileUrl, lookup):
  lineNum = -1
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


def get_generic_link(aList, formId, startFrom, index):
  if index == 0:
    before = "None"
    link = f"\"{aList[0]}\""
    text = f"\"guide.{startFrom:02d}\""
    after = f"Some(\"guide.{startFrom + 1:02d}\")" if len(aList) == 3 else "None"
  else:
    before = f"Some(\"guide.{startFrom:02d}\")"
    link = f"\"{aList[1]}\""
    text = f"\"guide.{startFrom+1:02d}\""
    after = f"Some(\"guide.{startFrom+2:02d}\")" if len(aList) == 4 else 'None'
  return f"<p>@genericLink(params, \"{formId}\", LinkTemplate({before}, {link}, {text}, {after}))</p>"


def get_message_with_affinity(formId, num):
  return f"@MessagesUtils.getMessagesWithAffinity(\"guide.{num:02d}\", \"{formId}\", {{params(\"langLocaleCode\")}}.toString, {{params(\"affinityGroup\")}}.toString)"


def get_split_lists(mList):
  if [i for i in mList if isinstance(i, str) and i.endswith(':')]:
    size = len(mList)
    idx_list = [idx for idx, val in enumerate(mList) if val.endswith(':')]
    res = [mList[i: j] for i, j in
           zip([0] + idx_list, idx_list +
               ([size] if idx_list[-1] != size else []))]
    return [x for x in res if x]
  else:
    return [mList]


def get_copyright():
  return ["@*",
          "\n* Copyright 2019 HM Revenue & Customs",
          "\n*",
          "\n* Licensed under the Apache License, Version 2.0 (the \"License\");",
          "\n* you may not use this file except in compliance with the License.",
          "\n* You may obtain a copy of the License at",
          "\n*",
          "\n*     http://www.apache.org/licenses/LICENSE-2.0",
          "\n*",
          "\n* Unless required by applicable law or agreed to in writing, software",
          "\n* distributed under the License is distributed on an \"AS IS\" BASIS,",
          "\n* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.",
          "\n* See the License for the specific language governing permissions and",
          "\n* limitations under the License.",
          "\n*@"]


def add_to_config(formId, url):
  fileUrl = digitalUrl + f"/conf/formCatalogue/{formId}.conf"
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  messageTemplate = f"\t\tcontinue_journey_uri = \"{url}\"\n"
  lineNumber = get_line_number(fileUrl, 'guide_page =')
  if lineNumber == -1:
    lineNumber = get_line_number(fileUrl, 'affinity_access') - 1  # if no guide_page to latch on to, put it above affinity_access section
  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()

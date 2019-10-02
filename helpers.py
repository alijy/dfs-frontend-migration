import re
import bs4
from nltk import flatten
from termcolor import colored

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


def get_data2(d):
  if isinstance(d, bs4.element.NavigableString):
    yield d
  if d.name == 'a':
    yield d['href']
  yield from [i for b in getattr(d, 'contents', []) for i in get_data(b)]


def get_data(d):
  if isinstance(d, bs4.element.NavigableString):
    yield d
  elif d.name == 'a':
    yield d['href']
    yield from [i for b in getattr(d, 'contents', []) for i in get_data(b)]
  elif d.name == 'ul' or d.name == 'li':
    yield [i for b in getattr(d, 'contents', []) for i in get_data(b)]
  else:
    yield from [i for b in getattr(d, 'contents', []) for i in get_data(b)]


def messageParser(message):
  return list(get_data(bs4.BeautifulSoup(message, 'html.parser')))


def isUrl(s):
  return s.startswith('/') or s.startswith('http') or s.startswith('www.')


def index_of_urls(aList):
  return [i for i in range(len(aList)) if isUrl(aList[i])]


def get_link_template(aList, id, startAt, idx):
  if len(idx) == 1:
    return startAt + len(aList) - 2, get_generic_link(aList, id, startAt, idx[0])
  else:
    c = startAt
    s = ''
    s += f"<p>"
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
    return c - 1, s


def get_list_template(i, formId, count, nested):
  c = count + 1
  s = ''
  if nested:
    s = f"\"guide.{c:02d}\", Seq("
  else:
    s = f"{get_message_with_affinity(formId, c)}"
    s += f"\n\n@nestedList(params, \"{formId}\", Seq("
  for index, item in enumerate(i[1]):
    if index > 0:
      s += ', '
    if len(item) == 1:
      c += 1
      s += f"\"guide.{c:02d}\""
    elif len(item) == 2 and item[0].endswith(':'):
      ts, c = get_list_template(item, formId, c, True)
      s += ts
    elif index_of_urls(item):
      c, ts = get_link_template(item, formId, c + 1, index_of_urls(item))
      s += ts
  s += ')' if nested else '))'
  return s, c


def get_partial_template(formId, count, key, value):
  s = ''
  for i in value:
    # print(f"{key} - {i}")
    if len(i) == 1:  # single <p> paragraph
      count += 1
      s += f"\n\n<p>{get_message_with_affinity(formId, count)}</p>"
    elif isinstance(i[0], str) and i[0].endswith(':'):  # a <ul> list
      if len(i) == 2:
        result, count = get_list_template(i, formId, count, False)
        s += f"\n\n<p>{result}</p>"
      else:
        result, count = get_list_template(i[:2], formId, count, False)
        s += f"\n\n<p>{result}</p>"
        count, ts = get_partial_template(formId, count, key, [i[2:]])
        s += f"{ts}"
    elif i == flatten(i) and index_of_urls(i):  # paragraph <p> with <a> links
      count, ts = get_link_template(i, formId, count + 1, index_of_urls(i))
      if len(index_of_urls(i)) == 1:
        s += f"\n\n<p>@genericLink(params, \"{formId}\", {ts})</p>"
      else:
        s += f"\n\n{ts}"
    else:
      print("ERROR : An unhandled variation was encountered when generating GUIDE PAGE TEMPLATE. This is most likely due to a missing html tag in guide page messages in dfs-frontend.")
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
  return f"LinkTemplate({before}, {link}, {text}, {after})"


def get_message_with_affinity(formId, num):
  return f"@MessagesUtils.getMessagesWithAffinity(\"guide.{num:02d}\", \"{formId}\", {{params(\"langLocaleCode\")}}.toString, {{params(\"affinityGroup\")}}.toString)"


def get_split_lists(mList):
  idx_list = [idx for idx, val in enumerate(mList) if isinstance(val, str) and val.endswith(':')]
  if idx_list:
    size = len(mList)
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


def enable_affinity(file, userType):
  s = open(file, 'r').read()
  s = s.replace(f"{userType.lower()} {{\n\t\t\t\tenabled = false", f"{userType.lower()} {{\n\t\t\t\tenabled = true")
  f = open(file, 'w')
  f.write(s)


def pInfo(message):
  print(colored("INFO : ", 'green'), colored(message, 'green'))


def pWarn(message):
  print(colored("WARN : ", 'magenta'), colored(message, 'yellow'))


def pError(message):
  print(colored("ERROR : ", 'red'), colored(message, 'red'))


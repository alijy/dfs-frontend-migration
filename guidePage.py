import os
import bs4
from helpers import frontendUrl, templateUrl, messageParser, isUrl, getLineNumber, \
  get_nested_list, get_message_with_affinity


def migrate_guide_messages(formId, formRef, uType, welshEnabled):
  if welshEnabled == 'true':
    migrate_guide_messages_for_lang(formId, formRef, uType, 'cy')
  return migrate_guide_messages_for_lang(formId, formRef, uType)


def migrate_guide_messages_for_lang(formId, formRef, uType, lang='en'):
  if lang == 'cy':
    importUrl = frontendUrl + '/conf/messages.cy'
    exportUrl = templateUrl + '/conf/messages.cy'
  else:
    importUrl = frontendUrl + '/conf/messages'
    exportUrl = templateUrl + '/conf/messages'

  # read guide messages from dfs-frontend
  f = open(importUrl, 'r')
  messages = f.read().split("\n")
  f.close()

  index = 0
  guideMessageList = []

  for i in range(0, len(messages)):
    if f"page.guide.header.{formId}" in messages[i]:  # expects header message to be the first one
      index = i

  while messages[index] and not messages[index].strip().startswith("#"):
    gm = messages[index].strip()
    if not gm.strip().startswith('page.guide'):
      if gm.strip() is not None:
        # guideMessageList[-1] += f"\n{gm}"
        guideMessageList[-1] += f"{gm}"
        index += 1
    else:
      guideMessageList.append(gm)
      index += 1

  print(f"guideMessageList: (count = {len(guideMessageList)}) {guideMessageList}")

  # write acknowledge messages into dfs-template-renderer
  messageStats = {}
  count = 0
  f = open(exportUrl, 'a')
  f.writelines(["\n\n###################################",
                f"\n# Guide Page {formId} {uType} #",
                "\n###################################"])

  for m in guideMessageList:
    m = m.replace('\\', '')
    if f"page.guide.header.{formId}" in m:
      f.write(f"\npage.guide.header.{formId}.{uType}={m.split('=')[1]}")
    else:
      print(f"m: {m}")
      if 'extraInfo' in m:
        mType = 'extraInfo'
      elif 'beforeStart' in m:
        mType = 'beforeStart'
      else:
        mType = 'list'
      parsedMessage = [messageParser(str(item)) for item in bs4.BeautifulSoup(m, 'html.parser')]
      messageStats[f"{mType}"] = parsedMessage
      print(f"Full-parsedMessage -> {parsedMessage}")
      for i in range(1, len(parsedMessage)):
        for msgString in parsedMessage[i]:
          if not isUrl(msgString):
            count += 1
            f.write(f"\nguide.{count:02d}.{formId}.{uType}={msgString}")

  return messageStats


# def decode_and_write_line(f, m):
#   pass
#
#
# def decode_and_write_section(f, m):
#   m = ['do this if:','thing one','thing two', 'thing', '/thing/three', 'three', '!']
#   if len(m) == 1:
#     print(f"<p>{m}</p>")
#   elif len(m) > 1:
#     if m[0].endswith(':'):
#       f.write(f"<p>{m}</p>")
#       # decode_and_write
#   else:
#     pass # to move on in


def messageUtilLine(count, formId):
  return f"@MessagesUtils.getMessagesWithAffinity(\"guide.{count}\", \"{formId}\", {{params(\"langLocaleCode\")}}.toString, {{params(\"affinityGroup\")}}.toString)"


def generate_guide_template(formId, userType, stats):
  folder = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates' + f"/{formId}"
  if not os.path.exists(folder):
    os.mkdir(folder)
    print(f"Folder {formId} created")
  if not os.path.exists(folder + f"/{userType}"):
    os.mkdir(folder + f"/{userType}")
    print(f"Folder {userType} created")
  if os.path.isfile(folder + f"/{userType}/{formId}.scala.html"):
    print('Warning: Acknowledgement template already exists')
  else:
    f = open(folder + f"/{userType}/{formId}.scala.html", 'w')
    f.writelines(["@*",
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
                  "\n*@"])

    f.writelines(["\n\n@import play.twirl.api.Html",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.templates.guidePageTemplates.helpers.genericHelpers.html._",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.utils._",
                  "\n\n@(params: Map[String, Any])",
                  f"\n\n@baseGenericGuidePageHeader(params, \"{formId}\")"])

    print(f"\n\nstats:{stats}")
    count = 1
    for key, value in stats.items():
      print(f"k = {key},     v = {value}")
      if key == 'list':
        f.write(f"\n\n@noLinkList(params, \"{formId}\", Seq(")
        for i in range(1, len(value)):
          if i > 1:
            f.write(", ")
          f.write(f"\"guide.{count:02d}\"")
          count += 1
        f.write("))")
      elif key == 'extraInfo':
        # TODO: need to make this section even more flexible
        for mLine in value[1:]:
          if isinstance(mLine[0], str):
            print(">>>>>>>>>>>>>> It is a string >>>>>>>>>>>>>>>>>")
            if mLine[0].endswith(':'):
              f.write(f"\n\n<p>{get_message_with_affinity(formId, count)}</p>")
              count += 1
              f.write(f"\n\n{get_nested_list(formId, count, len(mLine) - 1)}")
              count += len(mLine) - 1
            else:
              f.write(f"\n\n<p>")
              urlIndex = -99
              for k in range(len(mLine)):
                if isUrl(mLine[k]):
                  urlIndex = k
                  f.write(f" <a href=\"{mLine[k]}\">")
                else:
                  f.write(f"{get_message_with_affinity(formId, count)}")
                  count += 1
                  if k == urlIndex + 1:
                    f.write("</a>")
                    urlIndex = -99
              f.write("</p>")
          else:
            print("==============It is a list =================")

      elif key == 'beforeStart':
        f.write(f"\n\n@baseGenericGuidePageBody(params, \"{formId}\")")

        f.write(
          f"\n\n<p>@MessagesUtils.getMessagesWithAffinity(\"guide.{count:02d}\", \"{formId}\", {{params(\"langLocaleCode\")}}.toString, {{params(\"affinityGroup\")}}.toString)</p>")
        count += 1

        if len(value) > 2:
          f.write(f"\n\n@noLinkList(params, \"{formId}\", Seq(")
          for i in range(len(value[2])):
            if i > 0:
              f.write(", ")
            f.write(f"\"guide.{count:02d}\"")
            count += 1
          f.write("))")

    f.write("\n\n<p>@MessagesUtils.getCommonMessages(\"page.guide.youCanTrack\", {params(\"langLocaleCode\")}.toString) <a href=\"@Links.ptaLink\">@MessagesUtils.getCommonMessages(\"abandon.pta.link.msg\", {params(\"langLocaleCode\")}.toString)</a> </p>")
    f.close()

def update_guideTemplateLocator(formId, userType):
  fileUrl = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates/GuidePageTemplateLocator.scala'
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  contents.insert(37, f"\t\t\t\"{formId}.{userType}\"\t\t\t\t\t-> GuidePageTemplates.{userType.lower()}Templates,\n")

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()



def update_guideTemplates(formId, userType):
  fileUrl = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates/GuidePageTemplates.scala'
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  messageTemplate = f"\t\tMessageTemplate.create(\n\t\t\ttemplateId = \"{formId}.{userType}\",\n\t\t\thtmlTemplate = {formId}.{userType}.html.{formId}.f),\n"

  if userType == 'Organisation':
    lineNumber = getLineNumber(fileUrl, 'organisationTemplates')
  elif userType == 'Agent':
    lineNumber = getLineNumber(fileUrl, 'agentTemplates')
  else:
    lineNumber = getLineNumber(fileUrl, 'individualTemplates')

  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()


def update_guideTemplate_spec(formId, userType):
  fileUrl = templateUrl + '/test/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates/GuidePageTemplateLocatorSpec.scala'
  lineNumber = getLineNumber(fileUrl, 'guidePageTemplateLocator.templateGroups.keys')

  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  messageTemplate = f"\t\t\t\t\"{formId}.{userType}\",\n"
  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()


def guide_page_exists(formId, userType):
  folder = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates'
  return os.path.exists(f"{folder}/{formId}") and \
         os.path.exists(f"{folder}/{formId}/{userType.lower()}") and \
         os.path.isfile(f"{folder}/{formId}/{userType.lower()}/{formId}.scala.html")


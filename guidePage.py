import os
import bs4
from nltk import flatten

from helpers import frontendUrl, templateUrl, messageParser, isUrl, get_line_number, \
  get_nested_list, get_message_with_affinity, get_copyright, get_partial_template


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

  index = -1
  guideMessageList = []

  ifAgent = '.agent' if uType == 'Agent' else ''
  for i in range(0, len(messages)):
    if f"page.guide{ifAgent}.header.{formId}" in messages[i]:  # expects header message to be the first one
      index = i
      break

  while messages[index] and not messages[index].strip().startswith("#"):
    gm = messages[index].strip()
    if not gm.strip().startswith('page.guide'):
      if gm.strip() is not None:
        guideMessageList[-1] += f"{gm}"
        index += 1
    else:
      guideMessageList.append(gm)
      index += 1

  print(f"guideMessageList: (count = {len(guideMessageList)}) {guideMessageList}")

  # write guide page messages into dfs-template-renderer
  messageStats = {}
  count = 0
  f = open(exportUrl, 'a')
  f.writelines(["\n\n###################################",
                f"\n# Guide Page {formId} {uType} #",
                "\n###################################"])

  for m in guideMessageList:
    m = m.replace('\\', '')
    if f"page.guide{ifAgent}.header.{formId}" in m:
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
        for msgString in flatten(parsedMessage[i]):
          if not isUrl(msgString):
            count += 1
            f.write(f"\nguide.{count:02d}.{formId}.{uType}={msgString}")

  return messageStats


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
    print('Warning: Guide page template already exists')
  else:
    f = open(folder + f"/{userType}/{formId}.scala.html", 'w')
    f.writelines(get_copyright())
    f.writelines(["\n\n@import play.twirl.api.Html",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.templates.guidePageTemplates.helpers.genericHelpers.html._",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.utils._",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.models.LinkTemplate",
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
      elif key == 'extraInfo' or key == 'beforeStart':
        count, text = get_partial_template(formId, count, key, value)
        f.write(text)
      else:
        print("ERROR: The detected set of messages are not of types: header, list, extraInfo or beforeStart.")

    f.write("\n\n<p>@MessagesUtils.getCommonMessages(\"page.guide.youCanTrack\", {params(\"langLocaleCode\")}.toString) <a href=\"@Links.ptaLink\">@MessagesUtils.getCommonMessages(\"abandon.pta.link.msg\", {params(\"langLocaleCode\")}.toString)</a> </p>")
    f.close()

def update_guideTemplateLocator(formId, userType):
  fileUrl = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates/GuidePageTemplateLocator.scala'
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  lineNumber = get_line_number(fileUrl, "templateGroups: Map[String, Seq[MessageTemplate]]") + 1
  contents.insert(lineNumber, f"\t\t\t\"{formId}.{userType}\"\t\t\t\t\t-> GuidePageTemplates.{userType.lower()}Templates,\n")

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
  lineNumber = get_line_number(fileUrl, f"{userType.lower()}Templates")
  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()


def update_guideTemplate_spec(formId, userType):
  fileUrl = templateUrl + '/test/uk/gov/hmrc/dfstemplaterenderer/templates/guidePageTemplates/GuidePageTemplateLocatorSpec.scala'
  lineNumber = get_line_number(fileUrl, 'guidePageTemplateLocator.templateGroups.keys')

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


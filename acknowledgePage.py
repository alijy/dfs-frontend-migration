import re
import os
import bs4
from nltk import flatten
from helpers import sanitise, frontendUrl, templateUrl, get_line_number, get_copyright, add_to_config, pInfo, pWarn, \
  messageParser


def migrate_acknowledge_messages(formId, formRef, uType, welshEnabled):
  if welshEnabled == 'true':
    migrate_messages(formId, formRef, uType, 'cy')
  return migrate_messages(formId, formRef, uType)


def migrate_messages(formId, formRef, uType, lang = 'en'):
  if lang == 'cy':
    importUrl = frontendUrl + '/conf/messages.cy'
    exportUrl = templateUrl + '/conf/messages.cy'
  else:
    importUrl = frontendUrl + '/conf/messages'
    exportUrl = templateUrl + '/conf/messages'

  # read acknowledge messages from dfs-frontend
  f = open(importUrl, 'r')
  messages = f.read().split("\n")
  f.close()

  index = -1
  ackMessageList = []

  for i in range(0, len(messages)):
    if re.search(f"page.ack.title.{formId}" + r"\s*=", messages[i]) or re.search(f"page.ack.sent.{formId}" + r"\s*=", messages[i]):
      index = i
      break

  if index == -1:
    pWarn(f"no acknowledge page message was found")
    return []
  else:
    while messages[index] and not messages[index].strip().startswith("#"):
      am = messages[index]
      if not am.strip().startswith('page'):
        ackMessageList[-1] += f"{am}"
      else:
        ackMessageList.append(am)
      index += 1

    print(f"ackMessageList: {ackMessageList}")

    # write acknowledge messages into dfs-template-renderer
    ackCount = 0
    f = open(exportUrl, 'a')
    f.writelines(["\n\n##############################",
                  f"\n# Ack {formId} {uType} #",
                  "\n##############################"])

    if lang == 'cy':
      f.write(f"\nack.nextSteps.{formId}.{uType}=Camau nesaf")
    else:
      f.write(f"\nack.nextSteps.{formId}.{uType}=Next steps")

    parsedMessage = []
    for m in ackMessageList:
      m = m.replace('\\', '')
      if 'page.ack.sent' in m or 'page.ack.title' in m:
        f.write(f"\nack.submitted.{formId}.{uType}={m.split('=')[1]}")
      elif 'save_a_copy' in m.lower():
        pass
      elif 'button.text' in m.lower():
        f.writelines([f"\nack.tracking.{formId}.{uType}=",  # this is intentional to override the default value
                      f"\nlink.track-your-form.{formId}.{uType}={m.split('=')[1]}"])
      elif 'button.uri' in m.lower():
        add_to_config(formId, m.split('=', 1)[1])
        f.write(f"Note: Check that 'continue_journey_uri' is correctly added to {formId}.conf")
      elif f"what_happens_next.{formId}".lower() in m.lower():
        parsedMessage = [messageParser(str(item)) for item in bs4.BeautifulSoup(m, 'html.parser')]
        parsedMessage = sanitise(parsedMessage)
        print(f"parsed ack : {parsedMessage}")
        for i in flatten(parsedMessage[1:]):
          ackCount += 1
          f.write(f"\nack.{ackCount:02d}.{formId}.{uType}={i}")
      else:
        try:
          pWarn(f"{m.split('=')[0]} was ignored in acknowledge message migration")
        except:
          pWarn('An unhandled message was found in acknowledge messages')

    return parsedMessage


def generate_acknowledge_template(formId, userType, ml):
  folder = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/ackTemplates' + f"/{formId}"
  if not os.path.exists(folder):
    os.mkdir(folder)
    pInfo(f"Folder {formId} created")
  if not os.path.exists(folder + f"/{userType}"):
    os.mkdir(folder + f"/{userType}")
    pInfo(f"Folder {userType} created")
  if os.path.isfile(folder + f"/{userType}/{formId}.scala.html"):
    pWarn('Acknowledgement template already exists')
  else:
    f = open(folder + f"/{userType}/{formId}.scala.html", 'w')
    f.writelines(get_copyright())
    f.writelines(["\n\n@import uk.gov.hmrc.dfstemplaterenderer.utils._",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.templates.ackTemplates.helpers.html._",
                  "\n\n@(params: Map[String, Any])",
                  "\n\n@submissionCompleteBanner(params)",
                  "\n@downloadPdfLink(params)",
                  "\n@heading2(\"ack.nextSteps\",params)"])

    count = 0
    for i in ml[1:]:
      if not i:
        pass
      elif i == flatten(i):
        count += 1
        f.write(f"\n@paragraph(\"ack.{count:02d}\", params)")
      elif len(i) == 1:
        f.write(f"\n@unorderedList(Seq(")
        length = len(flatten(i))
        for j in range(length):
          if j > 0:
            f.write(', ')
          count += 1
          f.write(f"\"ack.{count:02d}\"")
        f.write('), params)')

    f.write("\n@ContinueJourneyButton(params)")
    if userType == 'Individual':
      f.write("\n@crossSelling(params)")

    f.close()


def update_ackTemplateLocator(formId, userType):
  fileUrl = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/ackTemplates/AckTemplateLocator.scala'
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  lineNumber = get_line_number(fileUrl, 'templateGroups: Map[String, Seq[MessageTemplate]]') + 1
  contents.insert(lineNumber, f"\t\t\t\"{formId}.{userType}\"\t\t\t\t-> AckTemplates.{userType.lower()}Templates,\n")

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()


def update_ackTemplates(formId, userType):
  fileUrl = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/ackTemplates/AckTemplates.scala'
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  messageTemplate = f"""\t\tMessageTemplate.create(
\t\t\ttemplateId = \"{formId}.{userType}\",
\t\t\thtmlTemplate = {formId}.{userType}.html.{formId}.f),\n"""
  lineNumber = get_line_number(fileUrl, f"{userType.lower()}Templates")
  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()


def update_ackTemplate_spec(formId, userType):
  fileUrl = templateUrl + '/test/uk/gov/hmrc/dfstemplaterenderer/templates/ackTemplates/AckTemplateLocatorSpec.scala'
  lineNumber = get_line_number(fileUrl, 'ackTemplateLocator.templateGroups.keys')

  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  messageTemplate = f"\t\t\t\t\"{formId}.{userType}\",\n"
  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()



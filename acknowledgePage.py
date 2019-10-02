import re
import os
from helpers import sanitise, frontendUrl, templateUrl, get_line_number, get_copyright, add_to_config, pInfo, pWarn


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

  ackIndex = 0
  ackMessageList = []

  for i in range(0, len(messages)):
    # if re.search(f"page.ack.title.{formId}=" in messages[i] or f"page.ack.sent.{formId}=" in messages[i]:
    if re.search(f"page.ack.title.{formId}" + r"\s*=", messages[i]) or re.search(f"page.ack.sent.{formId}" + r"\s*=", messages[i]):
      ackIndex = i

  if ackIndex == 0:
    pWarn(f"no acknowledge page message was found")
    return 0
  else:
    while messages[ackIndex] and not messages[ackIndex].strip().startswith("#"):
      ackMessage = messages[ackIndex]
      print(f"ackMessage : {ackMessage}")
      if not ackMessage.strip().startswith('page'):
        ackMessageList[-1] += f"\n{ackMessage}"
      else:
        ackMessageList.append(ackMessage)
      ackIndex += 1

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

    for m in ackMessageList:
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
      else:
        splitMessage = sanitise(m.split('=', 1)[1].split('\n'))
        for i in splitMessage:
          ackCount += 1
          f.write(f"\nack.{ackCount:02d}.{formId}.{uType}={i}")

    return ackCount


def generate_acknowledge_template(formId, userType, messageNum):
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

    for i in range(messageNum):
      f.write(f"\n@paragraph(\"ack.{i+1:02d}\", params)")

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



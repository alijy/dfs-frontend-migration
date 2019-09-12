from helpers import sanitise, frontendUrl, templateUrl
import os


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
  print(f"messages = {messages}")
  f.close()

  ackIndex = 0
  ackMessageList = []

  for i in range(0, len(messages)):
    if "acknowledgement" in messages[i].lower() and formRef.lower() in messages[i].lower():
      ackIndex = i + 2

  while not (messages[ackIndex] == "" or messages[ackIndex].strip().startswith("#")):
    ackMessage = messages[ackIndex]
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
      # TODO: update/change link.uri.track-your-form after DL-2350 is done
      f.write(f"\nlink.uri.track-your-form.{formId}.{uType}={m.split('=')[1]}")
    else:
      rawMesssage = sanitise(m.split("\n"))
      if len(rawMesssage) == 1:
        ackCount += 1
        f.write(f"\nack.{ackCount:02d}.{formId}.{uType}={rawMesssage[0].split('=')[1]}")
      else:
        for i in range(1, len(rawMesssage)):
          ackCount += 1
          f.write(f"\nack.{ackCount:02d}.{formId}.{uType}={rawMesssage[i]}")

  return ackCount


def generate_acknowledge_template(formId, userType, messageNum):
  folder = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/ackTemplates' + f"/{formId}"
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

    f.writelines(["\n\n@import uk.gov.hmrc.dfstemplaterenderer.utils._",
                  "\n@import uk.gov.hmrc.dfstemplaterenderer.templates.ackTemplates.helpers.html._",
                  "\n\n@(params: Map[String, Any])",
                  "\n\n@submissionCompleteBanner(params)",
                  "\n@downloadPdfLink(params)",
                  "\n@heading2(\"ack.nextSteps\",params)"])

    for i in range(messageNum):
      f.write(f"\n@paragraph(\"ack.{i+1:02d}\", params)")

    f.write("\n@trackAndTrace(params)")
    if userType == 'Individual':
      f.write("\n@crossSelling(params)")

    f.close()


def update_ackTemplateLocator(formId, userType):
  fileUrl = templateUrl + '/app/uk/gov/hmrc/dfstemplaterenderer/templates/ackTemplates/AckTemplateLocator.scala'
  f = open(fileUrl, 'r')
  contents = f.readlines()
  f.close()

  contents.insert(36, f"\t\t\t\"{formId}.{userType}\"\t\t\t\t-> AckTemplates.{userType.lower()}Templates,\n")

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

  if userType == 'Organisation':
    lineNumber = 121
  elif userType == 'Agent':
    lineNumber = 107
  else:
    lineNumber = 29

  contents.insert(lineNumber, messageTemplate)

  f = open(fileUrl, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()

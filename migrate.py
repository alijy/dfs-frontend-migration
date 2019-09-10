import ntpath
import os.path
import re
from pyhocon import ConfigFactory, ConfigMissingException

exportFilePath = '/Users/ali/code/hmrcdev/pool/dfs-digital-forms-frontend/conf/formCatalogue/CA72ASUB.conf'
formCatalogueUrl = "/Users/ali/code/hmrcdev/pool/dfs-digital-forms-frontend/conf/form-catalogue.conf"
importMessagesUrl = '/Users/ali/code/hmrcdev/pool/dfs-frontend/conf/messages'
exportMessagesUrl = '/Users/ali/code/hmrcdev/pool/dfs-template-renderer/conf/messages'

importFileName = 'migrateThis.conf'


# read form type reference from migrateThis.conf
f = open(importFileName, 'r')
fLine = f.readline().strip()
while fLine.startswith('#') or fLine == "":
  fLine = f.readline().strip()
formTypeRef = fLine.split(' ')[0].strip('{')
f.close()


# determine form ID from exportFilePath
exportFileName = ntpath.basename(exportFilePath)
formId = ntpath.splitext(exportFileName)[0]


# parse config file into a tree structure
conf = ConfigFactory.parse_file(importFileName)


if os.path.exists(exportFilePath):
  print(f"{exportFileName} already exists!\nNo automated migration is done!")
else:
  # initialise digital config file
  f = open(exportFilePath, 'w')
  f.writelines(["# Copyright 2019 HM Revenue & Customs\n",
                "#\n",
                "# Licensed under the Apache License, Version 2.0 (the \"License\");\n",
                "# you may not use this file except in compliance with the License.\n",
                "# You may obtain a copy of the License at\n",
                "#\n",
                "#     http://www.apache.org/licenses/LICENSE-2.0\n",
                "#\n",
                "# Unless required by applicable law or agreed to in writing, software\n",
                "# distributed under the License is distributed on an \"AS IS\" BASIS,\n",
                "# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n",
                "# See the License for the specific language governing permissions and\n",
                "# limitations under the License.\n",
                "\n",
                "forms {\n",
                "\t\n",
                f"\t{formTypeRef} {{\n",
                "\t\tenabled = true\n"])


  # add business category if available
  try:
    value = conf[formTypeRef]['business_category'][0]
    f.write(f"\n\t\tbusiness_category = [{value}]\n")
  except:
    print("Not found: business category")


  # add aem version if available
  try:
    value = conf[formTypeRef]['aem']['form_version']
  except:
    value = ""
    print("Not found: aem form version")
  finally:
    f.writelines(["\n\t\taem {",
                  f"\n\t\t\tform_version = \"{value}\"",
                  "\n\t\t}\n"])


  # add dms if available
  f.writelines(["\n\t\tdms {",
                "\n\t\t\tdms_metadata {"])

  # business area
  try:
    value = conf[formTypeRef]['dms']['dms_metadata']['business_area']
  except:
    value = ""
    print("Not found: DMS business area")
  finally:
    f.write(f"\n\t\t\t\tbusiness_area = \"{value}\"")

  # classification type
  try:
    value = conf[formTypeRef]['dms']['dms_metadata']['classification_type']
  except:
    value = ""
    print("Not found: DMS classification type")
  finally:
    f.write(f"\n\t\t\t\tclassification_type = \"{value}\"")


  # Welsh classification type
  f.write("\n\t\t\t\twelsh_classification_type = \"WLU-WCC-XDFSWelshLanguageService\"")


  # user id xpath
  f.writelines(["\n",
                "\n\t\t\t\t# The adaptive form field xpath to use when sending to DMS, used instead of the logged in users enrolment identifier like their UTR, NINO, ARN etc",
                "\n\t\t\t\tuser_id_path = \"\"",
                "\n\t\t\t}",
                "\n\t\t}\n"])


  # add draft details
  f.writelines(["\n\t\tdraft {",
                "\n\t\t\tkeep_for_days = 30",
                "\n\t\t}\n"])

  # add email details
  try:
    value = conf[formTypeRef]['email_notification']['email_template_id']
  except:
    value = ""
    print("Not found: email template")
  finally:
    f.writelines(["\n\t\temail {",
                  f"\n\t\t\ttemplate_id = \"{value}\"",
                  "\n\t\t}\n"])

  # add webchat details
  f.write("\n\t\twebchat {")
  try:
    value = conf[formTypeRef]['webchat_enabled']
    if value:
      f.write("\n\t\t\tenabled = true")
    else:
      f.write("\n\t\t\tenabled = false")
  except:
    print("Not found: webchat")
    f.write("\n\t\t\tenabled = false")
  f.write("\n\t\t}\n")

  # add welsh language
  f.writelines(["\n\t\tlanguage {",
                "\n\t\t\twelsh {"])
  try:
    value = conf[formTypeRef]['language']['welsh']['enabled']
    if value:
      f.write("\n\t\t\t\tenabled = true")
    else:
      f.write("\n\t\t\t\tenabled = false")
  except:
    print("Not found: Welsh language")
    f.write("\n\t\t\t\tenabled = false")

  f.writelines(["\n\t\t\t}",
                "\n\t\t}\n"])

  # add affinity access
  agentAccess = 'false'
  individualAccess = 'false'
  organisationAccess = 'false'
  oneTimePass = 'false'
  try:
    value = conf[formTypeRef]['authentication']['type']
    if value == 'GGIV':
      individualAccess = 'true'
      userType = 'Individual'
    elif value == 'GGW':
      organisationAccess = 'true'
      userType = 'Organisation'
    elif value == 'GGWANY':
      agentAccess = 'true'
      userType = 'Agent'
    elif value == 'OTP':
      individualAccess = 'true'
      oneTimePass = 'true'
      userType = 'Individual'
  except:
    print("Not found: Affinity Access")
  finally:
    f.writelines(["\n\t\taffinity_access {",
                  "\n\t\t\tagent {",
                  f"\n\t\t\t\tenabled = {agentAccess}",
                  "\n\t\t\t}",
                  "\n\t\t\tindividual {",
                  f"\n\t\t\t\tenabled = {individualAccess}"])
    if individualAccess == 'true':
      f.write(f"\n\t\t\t\tone_time_pass = {oneTimePass}")

    f.writelines(["\n\t\t\t}",
                  "\n\t\t\torganisation {",
                  f"\n\t\t\t\tenabled = {organisationAccess}"])

    if organisationAccess == 'true':
      f.write("\n\t\t\t\tenrolment_required = \"ANY-UTR\"")

    f.writelines(["\n\t\t\t}",
                  "\n\t\t}\n"])


  # add guide page
  try:
    value = conf[formTypeRef]['start_page']
  except:
    value = ""
    print("Not found: guide page")
  finally:
    f.write(f"\n\t\tguide_page = \"{value}\"\n")


  # close brackets and file
  f.writelines(["\n\t}",
                "\n}"])
  f.close()

  print("Config file created")

  # update form catalogue
  f = open(formCatalogueUrl, 'a')
  f.write(f"\ninclude \"formCatalogue/{exportFileName}\"")
  f.close()
  print("Form catalogue updated")


  # migrate EN messages
  # read acknowledge messages from dfs-frontend
  f = open(importMessagesUrl, 'r')
  messages = f.read().split("\n")
  f.close()

  ackIndex = 0
  ackMessageList = []

  for i in range(0, len(messages)):
    if "Acknowledgement" in messages[i] and formTypeRef in messages[i]:
      print(messages[i].strip())
      ackIndex = i + 2

  while not (messages[ackIndex] == "" or messages[ackIndex].strip().startswith("#")):
    ackMessage = messages[ackIndex]
    # while not messages[ackIndex + 1].strip().startswith('page'):
    #   ackMessage += f"\n{messages[ackIndex + 1]}"
    #   ackIndex += 1

    if not ackMessage.strip().startswith('page'):
      ackMessageList[-1] += f"\n{ackMessage}"
    else:
      ackMessageList.append(ackMessage)
    ackIndex += 1

  print(ackMessageList)

  # write acknowledge messages into dfs-template-renderer
  ackCount = 0
  f = open(exportMessagesUrl, 'a')
  f.writelines(["\n\n##############################",
                f"\n# Ack {formId} {userType} #",
                "\n##############################"])

  f.write(f"\nack.nextSteps.{formId}.{userType}=Next steps")


  def sanitise(message_list):
    result = []
    cleaner = re.compile('<.*?>')
    for m in message_list:
      clean_text = re.sub(cleaner, '', m).strip("\\").strip()
      if clean_text != "":
        result.append(clean_text)
    return result

  for m in ackMessageList:
    if 'sent' in m:
      f.write(f"\nack.submitted.{formId}.{userType}={m.split('=')[1]}")
    elif 'save a copy' in m:
      pass
    else:
      rawMesssage = sanitise(m.split("\n"))
      if len(rawMesssage) == 1:
        ackCount += 1
        f.write(f"\nack.{ackCount:02d}.{formId}.{userType}={rawMesssage[0].split('=')[1]}")
      else:
        for i in range(1, len(rawMesssage)):
          ackCount += 1
          f.write(f"\nack.{ackCount:02d}.{formId}.{userType}={rawMesssage[i]}")


  print("\nDone!")

import ntpath
import os.path
from pyhocon import ConfigFactory
from acknowledgePage import migrate_acknowledge_messages, generate_acknowledge_template, update_ackTemplateLocator, \
  update_ackTemplates, update_ackTemplate_spec
from emailHelper import migrate_emails
from formCatalogue import *
from guidePage import migrate_guide_messages, generate_guide_template, update_guideTemplateLocator, \
  update_guideTemplates, update_guideTemplate_spec, guide_page_exists
from helpers import digitalUrl

# exportFilePath = digitalUrl + '/conf/formCatalogue/CA72ASUB.conf'
# exportFilePath = digitalUrl + '/conf/formCatalogue/CBOptIn.conf'
exportFilePath = digitalUrl + '/conf/formCatalogue/PT_CertOfRes.conf'
# exportFilePath = digitalUrl + '/conf/formCatalogue/TC600SUB.conf'
formCatalogueUrl = digitalUrl + '/conf/form-catalogue.conf'
importFileName = 'migrationConfig.conf'


# read form type reference from migrationConfig
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
  print(f"INFO : Config file {exportFileName} already exists. No migration is done!")
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
    print("WARN: business category NOT found in config file")

  # add aem version if available
  value = ""
  try:
    value = conf[formTypeRef]['aem']['form_version']
  except:
    print("WARN : aem form version NOT found in config file")
  finally:
    f.writelines(["\n\t\taem {",
                  f"\n\t\t\tform_version = \"{value}\"",
                  "\n\t\t}\n"])

  # add dms if available
  f.writelines(["\n\t\tdms {",
                "\n\t\t\tdms_metadata {"])

  # business area
  value = ""
  try:
    value = conf[formTypeRef]['dms']['dms_metadata']['business_area']
  except:
    print("WARN : DMS business area NOT found in config file")
  finally:
    f.write(f"\n\t\t\t\tbusiness_area = \"{value}\"")

  # classification type
  value = ""
  try:
    value = conf[formTypeRef]['dms']['dms_metadata']['classification_type']
  except:
    print("WARN : DMS classification type NOT found in config file")
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
    print("WARN : email template NOT found in config file")
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
    print("WARN : webchat NOT found in config file")
    f.write("\n\t\t\tenabled = false")
  f.write("\n\t\t}\n")

  # add welsh language
  f.writelines(["\n\t\tlanguage {",
                "\n\t\t\twelsh {"])
  welshEnabled = 'false'
  try:
    value = conf[formTypeRef]['language']['welsh']['enabled']
    if value:
      welshEnabled = 'true'
  except:
    print("WARN : Welsh language NOT found in config file")
  finally:
    f.write(f"\n\t\t\t\tenabled = {welshEnabled}")

  f.writelines(["\n\t\t\t}",
                "\n\t\t}\n"])

  # add affinity access
  agentAccess = 'false'
  individualAccess = 'false'
  organisationAccess = 'false'
  oneTimePass = 'false'
  userType = 'Individual'  # default
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
    print("WARN : Affinity Access NOT found in config file")
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
    print("WARN : guide page NOT found in config file")
  finally:
    f.write(f"\n\t\tguide_page = \"{value}\"\n")

  # close brackets and file
  f.writelines(["\n\t}",
                "\n}"])
  f.close()

  print(f"INFO : SUCCESS - Config file created - id: {formId} , ref: {formTypeRef} , user: {userType}")

  update_form_catalogue(formId)
  print(f"INFO : SUCCESS - Form catalogue updated")

  messageCount = migrate_acknowledge_messages(formId, formTypeRef, userType, welshEnabled)
  print(f"INFO : SUCCESS - Acknowledgement page messages migrated")

  generate_acknowledge_template(formId, userType, messageCount)
  print(f"INFO : SUCCESS - Acknowledgement page template created")

  update_ackTemplateLocator(formId, userType)
  print(f"INFO : SUCCESS - ackTemplateLocator updated")

  update_ackTemplates(formId, userType)
  print(f"INFO : SUCCESS - ackTemplates updated")

  update_ackTemplate_spec(formId, userType)
  print(f"INFO : SUCCESS - ackTemplate_spec updated")


  # read guide page type for guide page migration
  guidePageType = ''
  try:
    guidePageType = conf[formTypeRef]['guide_page_type']
  except:
    pass
  if guidePageType == 'generic':
    if not guide_page_exists(formId, userType):
      guideStats = migrate_guide_messages(formId, formTypeRef, userType, welshEnabled)
      # guideStats = migrate_guide_messages(formId, formTypeRef, userType, 'false')  # TODO: replace with above later
      print(f"INFO : SUCCESS - Guide page messages migrated")

      generate_guide_template(formId, userType, guideStats)
      print(f"INFO : SUCCESS - Guide page template created")

      update_guideTemplateLocator(formId, userType)
      print(f"INFO : SUCCESS - guideTemplateLocator updated")

      update_guideTemplates(formId, userType)
      print(f"INFO : SUCCESS - guideTemplates updated")

      update_guideTemplate_spec(formId, userType)
      print(f"INFO : SUCCESS - guideTemplate_spec updated")
    else:
      print("INFO : Guide Page already exists!")
  elif guidePageType == 'tes':
    print("WARN : This is a TES form. You need to migrate the guide page manually!")
  else:
    print("WARN : I couldn't find guide_page_type in the config file")

  respond = migrate_emails(formId, formTypeRef, welshEnabled)
  print(f"INFO : {respond}")

  print("\n\nINFO : *** Migration Process Completed. ***")

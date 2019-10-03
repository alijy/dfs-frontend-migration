import ntpath
import os.path
from pyhocon import ConfigFactory
from acknowledgePage import migrate_acknowledge_messages, generate_acknowledge_template, update_ackTemplateLocator, \
  update_ackTemplates, update_ackTemplate_spec
from emailHelper import migrate_emails
from formCatalogue import *
from guidePage import migrate_guide_messages, generate_guide_template, update_guideTemplateLocator, \
  update_guideTemplates, update_guideTemplate_spec, guide_page_exists
from helpers import digitalUrl, get_line_number, pWarn, pInfo, pError

# exportFilePath = digitalUrl + '/conf/formCatalogue/CA72ASUB.conf'
# exportFilePath = digitalUrl + '/conf/formCatalogue/CBOptIn.conf'
# exportFilePath = digitalUrl + '/conf/formCatalogue/PT_CertOfRes.conf'
# exportFilePath = digitalUrl + '/conf/formCatalogue/TC600SUB.conf'
exportFilePath = digitalUrl + '/conf/formCatalogue/TC122SUB.conf'
exportFilePath = digitalUrl + '/conf/formCatalogue/P11DBSUB.conf'
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

s = "\t\n" + f"\t{formTypeRef} {{\n" + "\t\tenabled = true\n"

# add business category if available
try:
  value = conf[formTypeRef]['business_category'][0]
  s += f"\n\t\tbusiness_category = [{value}]\n"
except:
  pWarn("business category NOT found in config file")


# add aem version if available
value = ""
try:
  value = conf[formTypeRef]['aem']['form_version']
except:
  pWarn("aem form version NOT found in config file")
finally:
  s += "\n\t\taem {" +\
       f"\n\t\t\tform_version = \"{value}\"" +\
       "\n\t\t}\n"

# add dms if available
s += "\n\t\tdms {" +\
     "\n\t\t\tdms_metadata {"

# business area
value = ""
try:
  value = conf[formTypeRef]['dms']['dms_metadata']['business_area']
except:
  pWarn("DMS business area NOT found in config file")
finally:
  s += f"\n\t\t\t\tbusiness_area = \"{value}\""

# classification type
value = ""
try:
  value = conf[formTypeRef]['dms']['dms_metadata']['classification_type']
  print(f"classification (type: {type(value)}) = {value}")
except:
  pWarn("DMS classification type NOT found in config file")
finally:
  s += f"\n\t\t\t\tclassification_type = "
  if isinstance(value, str):
    s += f"\"{value}\""
  elif isinstance(value, list):
    s += '['
    for i in range(len(value)):
      if i > 0:
        s += ','
      for k, v in value[i].items():
        s += f"\n\t\t\t\t\t{{{k} = \"{v}\"}}"
    s += '\n\t\t\t\t]'
  else:
    pError('DMS classification type is not recognised')


# Welsh classification type
s += "\n\t\t\t\twelsh_classification_type = \"WLU-WCC-XDFSWelshLanguageService\""


# user id xpath
s += "\n" +\
     "\n\t\t\t\t# The adaptive form field xpath to use when sending to DMS, used instead of the logged in users enrolment identifier like their UTR, NINO, ARN etc" +\
     "\n\t\t\t\tuser_id_path = \"\"" +\
     "\n\t\t\t}" +\
     "\n\t\t}\n"


# add draft details
s += "\n\t\tdraft {" +\
     "\n\t\t\tkeep_for_days = 30" +\
     "\n\t\t}\n"

# add email details
try:
  value = conf[formTypeRef]['email_notification']['email_template_id']
except:
  value = ""
  pWarn("email template NOT found in config file")
finally:
  s += "\n\t\temail {" +\
       f"\n\t\t\ttemplate_id = \"{value}\"" +\
       "\n\t\t}\n"

# add webchat details
s += "\n\t\twebchat {"
try:
  value = conf[formTypeRef]['webchat_enabled']
  if value:
    s += "\n\t\t\tenabled = true"
  else:
    s += "\n\t\t\tenabled = false"
except:
  pWarn("webchat NOT found in config file")
  s += "\n\t\t\tenabled = false"
s += "\n\t\t}\n"

# add welsh language
s += "\n\t\tlanguage {" +\
     "\n\t\t\twelsh {"
welshEnabled = 'false'
try:
  value = conf[formTypeRef]['language']['welsh']['enabled']
  if value:
    welshEnabled = 'true'
except:
  pWarn("Welsh language NOT found in config file")
finally:
  s += f"\n\t\t\t\tenabled = {welshEnabled}"

s += "\n\t\t\t}" +\
     "\n\t\t}\n"

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
  pWarn("authentication type NOT found in config file")
finally:
  s += "\n\t\taffinity_access {" +\
       "\n\t\t\tagent {" +\
       f"\n\t\t\t\tenabled = {agentAccess}" +\
       "\n\t\t\t}" +\
       "\n\t\t\tindividual {" +\
       f"\n\t\t\t\tenabled = {individualAccess}"
  if individualAccess == 'true':
    s += f"\n\t\t\t\tone_time_pass = {oneTimePass}"

  s += "\n\t\t\t}" +\
       "\n\t\t\torganisation {" +\
       f"\n\t\t\t\tenabled = {organisationAccess}"

  if organisationAccess == 'true':
    s += "\n\t\t\t\tenrolment_required = \"ANY-UTR\""

  s += "\n\t\t\t}" +\
       "\n\t\t}\n"

# Audit survey identifier
if userType == 'Agent':
  value = ""
  try:
    value = conf[formTypeRef]['audit']['survey']['identifier']
    s += "\n\t\taudit {" + "\n\t\t\tsurvey {" + f"\n\t\t\t\tidentifier = \"{value}\"" + "\n\t\t\t}" + "\n\t\t}\n"
  except:
    pWarn("Audit survey identifier NOT found in config file")

# add guide page
try:
  value = conf[formTypeRef]['start_page']
except:
  value = ""
  pWarn("guide page NOT found in config file")
finally:
  s += f"\n\t\tguide_page = \"{value}\"\n"

# close bracket
s += "\n\t}"


if os.path.exists(exportFilePath):
  pInfo(f"Config file {exportFileName} already exists")
  f = open(exportFilePath, 'r')
  contents = f.readlines()
  f.close()

  lineNumber = get_line_number(exportFilePath, "forms {")
  contents.insert(lineNumber, f"{s}\n\n")

  f = open(exportFilePath, 'w')
  contents = "".join(contents)
  f.write(contents)
  f.close()
else:
  update_form_catalogue(formId)
  pInfo(f"SUCCESS - Form catalogue updated")

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
                f"forms {{\n{s}\n}}"])
  f.close()

pInfo(f"SUCCESS - Config file created - id: {formId} , ref: {formTypeRef} , user: {userType}")


messageCount = migrate_acknowledge_messages(formId, formTypeRef, userType, welshEnabled)

if messageCount > 0:
  pInfo(f"SUCCESS - Acknowledgement page messages migrated")
  generate_acknowledge_template(formId, userType, messageCount)
  pInfo(f"SUCCESS - Acknowledgement page template created")

update_ackTemplateLocator(formId, userType)
pInfo(f"SUCCESS - ackTemplateLocator updated")

update_ackTemplates(formId, userType)
pInfo(f"SUCCESS - ackTemplates updated")

update_ackTemplate_spec(formId, userType)
pInfo(f"SUCCESS - ackTemplate_spec updated")


respond = migrate_emails(formId, formTypeRef, welshEnabled)
if 'SUCCESS' in respond:
  pInfo(respond)
else:
  pWarn(respond)

# read guide page type for guide page migration
guidePageType = ''
try:
  guidePageType = conf[formTypeRef]['guide_page_type']
except:
  pass
if guidePageType == 'generic':
  if not guide_page_exists(formId, userType):
    guideStats = migrate_guide_messages(formId, formTypeRef, userType, welshEnabled)
    pInfo(f"SUCCESS - Guide page messages migrated")

    generate_guide_template(formId, userType, guideStats)
    pInfo(f"SUCCESS - Guide page template created")

    update_guideTemplateLocator(formId, userType)
    pInfo(f"SUCCESS - guideTemplateLocator updated")

    update_guideTemplates(formId, userType)
    pInfo(f"SUCCESS - guideTemplates updated")

    update_guideTemplate_spec(formId, userType)
    pInfo(f"SUCCESS - guideTemplate_spec updated")
  else:
    pInfo("Guide Page already exists!")
elif guidePageType == 'tes':
  pWarn("This is a TES form. You need to migrate the guide page manually!")
else:
  pWarn("I couldn't find guide_page_type in the config file")

pInfo("*** Migration Process Completed ***")

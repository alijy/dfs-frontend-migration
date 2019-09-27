from helpers import frontendUrl, digitalUrl, get_line_number


def migrate_emails(formId, formRef, welshEnabled):
  if welshEnabled == 'true':
    migrate_messages(formId, formRef, 'cy')
  return migrate_messages(formId, formRef)


def migrate_messages(formId, formRef, lang='en'):
  if lang == 'cy':
    importUrl = frontendUrl + '/conf/messages.cy'
    exportUrl = digitalUrl + '/conf/messages.cy'
  else:
    importUrl = frontendUrl + '/conf/messages'
    exportUrl = digitalUrl + '/conf/messages'

  # check if email messages already exist
  lineNumber = get_line_number(exportUrl, f"email.subject.{formRef}=")
  if lineNumber == -1:

    # read guide messages from dfs-frontend
    f = open(importUrl, 'r')
    messages = f.read().split("\n")
    f.close()

    for i in range(0, len(messages)):
      if f"email.subject.{formId}" in messages[i]:  # expects header message to be the first one
        index = i

    f = open(exportUrl, 'a')
    f.write(f"""
\n################################################################
# email content - {formRef} #
################################################################""")

    while messages[index] and not messages[index].strip().startswith("#"):
      em = messages[index].strip()
      em = em.replace(f"{formId}", f"{formRef}")
      f.write(f"\n{em}")
      index += 1
    f.close()
    return 'SUCCESS - emails messages migrated'
  else:
    return 'emails messages already migrated'



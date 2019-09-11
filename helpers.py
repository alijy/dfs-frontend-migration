import re


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

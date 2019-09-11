from helpers import digitalUrl


def update_form_catalogue(formId):
  formCatalogueUrl = digitalUrl + '/conf/form-catalogue.conf'
  f = open(formCatalogueUrl, 'a')
  f.write(f"\ninclude \"formCatalogue/{formId}.conf\"")
  f.close()
  print("Form catalogue updated")

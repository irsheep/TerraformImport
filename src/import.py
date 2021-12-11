import json

# JSON data exported from the provider, for the resources to import
JSON_DATA_FILE = "data/provider_data.json"
# Output script for 'terraform import'
TERRAFORM_IMPORT_SCRIPT = "data/import.sh"
# Skeleton .tf file for the imported resources
TERRAFORM_OUTPUT_FILE = "data/import.tf"
# Terraform provider resource stype
TF_RESOURCE_TYPE = "azurerm_backup_protected_file_share"
# Provider resource filter
PROVIDER_RESOURCE_TYPE = "AzureFileShare"
# Dot path to the resource name
PROVIDER_RESOURCE_NAME_KEY = "properties.friendlyName"

# Loads json data from a file
def LoadJsonFile(fileName):
  fileHandle = open(fileName, "r")
  data = fileHandle.read()
  return json.loads(data)

# Writes an array to a text file
def WriteDataToFile(filename, data):
  with open(filename, "w") as fileHandle:
    for element in data:
      fileHandle.write('%s\n' % element)

# Get the value from a Dict a key in a dot path "a.b.c" 
def GetDictValueFromDotKeyPath(object, dotKeyPath):
  if isinstance(object, str): return object
  if isinstance(dotKeyPath, str): dotKeyPath = dotKeyPath.split(".")
  if dotKeyPath is None: return 1
  if len(dotKeyPath) == 0: return 2
  if len(dotKeyPath) == 1:
    if isinstance(dotKeyPath, str):
      return 6
  if dotKeyPath[0] in object.keys():
    if len(dotKeyPath) == 1: return object[dotKeyPath[0]]
    key = dotKeyPath[0]
    dotKeyPath.pop(0)
    return GetDictValueFromDotKeyPath(object[key], dotKeyPath)
  else:
    return 3

# Entrypoint
def main():
  data = LoadJsonFile(JSON_DATA_FILE)
  importData=[]
  terraformData=[]
  for resource in data:
    if PROVIDER_RESOURCE_TYPE in resource['name']:
      TF_RESOURCE_NAME=GetDictValueFromDotKeyPath(resource, PROVIDER_RESOURCE_NAME_KEY)
      PROVIDER_RESOURCE_ID=resource['id']
      importData.append(f"terraform import {TF_RESOURCE_TYPE}.{TF_RESOURCE_NAME} {PROVIDER_RESOURCE_ID}")
      terraformData.append(f"resource \"{TF_RESOURCE_TYPE}\" \"{TF_RESOURCE_NAME}\" {{}}\n")
  WriteDataToFile(TERRAFORM_IMPORT_SCRIPT, importData)
  WriteDataToFile(TERRAFORM_OUTPUT_FILE, terraformData)

if __name__ == "__main__":
  main()

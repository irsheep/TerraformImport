import json

# JSON data exported from the provider, for the resources to import
JSON_DATA_FILE = "data/provider_data.json"
# Output script for 'terraform import'
TERRAFORM_IMPORT_SCRIPT = "data/import.sh"
# Skeleton .tf file for the imported resources
TERRAFORM_SKELETON_TF_FILE = "data/skeleton.tf"
# Final terraform file with full imported resources
TERRAROFM_RESOURCE_TF_FILE="data/resources.tf"
# Terraform state file, this can be the latest copy
TERRAFORM_STATE_FILE="data/terraform.tfstate"
# JSON file with attrubites per resource to import to TERRAROFM_RESOURCE_TF_FILE
TERRAFORM_MAPPING_FILE="data/mapping.json"
# Terraform provider resource type
TERRAFORM_RESOURCE_TYPE = "azurerm_backup_protected_file_share"
# Provider resource filter
PROVIDER_RESOURCE_TYPE = "AzureFileShare"
# Dot path to the resource name
PROVIDER_RESOURCE_NAME_KEY = "properties.friendlyName"

# Loads json data from a file
def LoadJsonFile(fileName):
  fileHandle = open(fileName, "r")
  data = fileHandle.read()
  return json.loads(data)

def LoadTextFile(fileName):
  fileHandle = open(fileName, "r")
  data = fileHandle.read()
  return data

# Writes an array to a text file
def WriteArrayToFile(filename, data):
  with open(filename, "w") as fileHandle:
    for element in data:
      fileHandle.write('%s\n' % element)

def WriteTextToFile(filename, data):
  with open(filename, "w") as fileHandle:
    fileHandle.write(data)

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

def CreateImportFiles():
  data = LoadJsonFile(JSON_DATA_FILE)
  importData=[]
  terraformData=[]
  for resource in data:
    if PROVIDER_RESOURCE_TYPE in resource['name']:
      TF_RESOURCE_NAME=GetDictValueFromDotKeyPath(resource, PROVIDER_RESOURCE_NAME_KEY)
      PROVIDER_RESOURCE_ID=resource['id']
      importData.append(f"terraform import {TERRAFORM_RESOURCE_TYPE}.{TF_RESOURCE_NAME} {PROVIDER_RESOURCE_ID}")
      terraformData.append(f"resource \"{TERRAFORM_RESOURCE_TYPE}\" \"{TF_RESOURCE_NAME}\" {{}}\n")
  WriteArrayToFile(TERRAFORM_IMPORT_SCRIPT, importData)
  WriteArrayToFile(TERRAFORM_SKELETON_TF_FILE, terraformData)

def FindResourceInstancesFromTfstate(tfState, type, name):
  for resource in tfState['resources']:
    if resource['type'] == type and resource['name'] == name:
      # instances[0] is a terrible assumption
      return resource['instances'][0]['attributes']
  return False

def CastValueToTerraformType(value):
  if value == None: return "null"
  if isinstance(value, bool): return f"{str(value).lower()}"
  if isinstance(value, int): return int(value)
  return f'"{value}"'

def ImportFromTfState():
  terraformStateData = LoadJsonFile(TERRAFORM_STATE_FILE)
  importData = LoadTextFile(TERRAFORM_SKELETON_TF_FILE)
  mappings = LoadJsonFile(TERRAFORM_MAPPING_FILE)
  terraformResourceData = ""
  for line in importData.split("\n"):
    if line != "":
      [ a, resourceType, resourceName, d] = line.replace('"',"").split()
      tfstateInstanceAttributes = FindResourceInstancesFromTfstate(terraformStateData, resourceType, resourceName)
      terraformResourceData = f'{terraformResourceData}resource "{resourceType}" "{resourceName}" {{'
      if tfstateInstanceAttributes:
        for key in mappings[resourceType]:
          terraformResourceData = f'{terraformResourceData}\n  {key} = {CastValueToTerraformType(tfstateInstanceAttributes[key])}'
        terraformResourceData = f'{terraformResourceData}\n'
      terraformResourceData = f'{terraformResourceData}}}\n\n'
  WriteTextToFile(TERRAROFM_RESOURCE_TF_FILE, terraformResourceData)

# Entrypoint
def main():
  CreateImportFiles()
  ImportFromTfState()

if __name__ == "__main__":
  main()
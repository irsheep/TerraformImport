#!/usr/bin/env python

import json
import argparse
import configparser
from json.encoder import JSONEncoder
import re
from jsonpath_ng import jsonpath, parse

# JSON data exported from the provider, for the resources to import
JSON_DATA_FILE = ""
# Output script for 'terraform import'
TERRAFORM_IMPORT_SCRIPT = ""
# Skeleton .tf file for the imported resources
TERRAFORM_SKELETON_TF_FILE = ""
# Final terraform file with full imported resources
TERRAFORM_RESOURCE_TF_FILE = ""
# Terraform state file, this can be the latest copy
TERRAFORM_STATE_FILE = ""
# JSON file with attrubites per resource to import to TERRAROFM_RESOURCE_TF_FILE
TERRAFORM_MAPPING_FILE = ""
# Terraform provider resource type
TERRAFORM_RESOURCE_TYPE = ""
#
PROVIDER_RESOURCE_ROOT = ""
# Provider resource filter
PROVIDER_RESOURCE_TYPE = ""
#
PROVIDER_RESOURCE_ID_KEY = ""
# Dot path to the resource name
PROVIDER_RESOURCE_NAME_KEY = ""

"""
   Class: TerraformEncoder

   Description: Converts a JSON object (dict) to Terraform syntax
     Invoke as ```json.dumps(myJsonObject, cls=TerraformEncoder)```.
"""
class TerraformEncoder(json.JSONEncoder):
  def default(self, jsonString):
    return jsonString
  def encode(self, jsonObject):
    self.indent=2
    self.key_separator = " = "
    self.item_separator = ""
    terraformObjectString:str = ""
    jsonEncodedString = json.JSONEncoder.encode(self, jsonObject)
    regex = re.compile(r"\"(.+)\"\s+\=\s(.*)")
    for line in jsonEncodedString.split("\n"):
      line = regex.sub(r"\g<1> = \g<2>", line)
      terraformObjectString = f"{terraformObjectString}{line}\n"
    return terraformObjectString.rstrip("\n")

"""
  Function: LoadJsonFile

  Description: Reads the content of a JSON file and returns it as a Dict.

  Parameters:
    - fileName: Path and name of the file to load
  
  Return: A Dict with the data.
"""
def LoadJsonFile(fileName):
  fileHandle = open(fileName, "r")
  data = fileHandle.read()
  return json.loads(data)

"""
  Function: LoadTextFile

  Description: Loads the contents of a file to a string.

  Parameters:
    - fileName: Path and name of the file to load
  
  Return: A the contents of the file.
"""
def LoadTextFile(fileName):
  fileHandle = open(fileName, "r")
  data = fileHandle.read()
  return data

"""
  Function: WriteArrayToFile

  Description: Writes the contents of an array to a file, where each element is a new line, 
    overwriting the contents of the file.

  Parameters:
    - fileName: Path and name of the file to write to
    - data: Array with data
"""
def WriteArrayToFile(filename, data):
  with open(filename, "w") as fileHandle:
    for element in data:
      fileHandle.write('%s\n' % element)

"""
  Function: WriteTextToFile

  Description: Writes a text string to a file, overwiting its contents.

  Parameters:
    - fileName: Path and name of the file to write to
    - data: Data to be writen to the file
"""
def WriteTextToFile(filename, data):
  with open(filename, "w") as fileHandle:
    fileHandle.write(data)

"""
  Function: CreateAzureImportFiles

  Description: Creates a script with "terraform import <resource> <id>" command syntaxt to import the required resources to 
    the Terraform state file and creates also a skeleton terraform (.tf) file with the resources that will be
    imported.
"""
def CreateAzureImportFiles():
  data = LoadJsonFile(JSON_DATA_FILE)
  importData=[]
  terraformData=[]
  for resource in data:
    if PROVIDER_RESOURCE_TYPE in resource['name']:
      if re.search(r":", PROVIDER_RESOURCE_NAME_KEY):
        [ jsonPath, keyName ] = PROVIDER_RESOURCE_NAME_KEY.split(":")
        TF_RESOURCE_NAME=GetValueFromKey(GetResourceValueByKeyPath(resource, f"$..{jsonPath}" ), keyName)
      else:
        TF_RESOURCE_NAME=GetResourceValueByKeyPath(resource, f"$..{PROVIDER_RESOURCE_NAME_KEY}")
      PROVIDER_RESOURCE_ID=resource['id']
      importData.append(f"terraform import {TERRAFORM_RESOURCE_TYPE}.{TF_RESOURCE_NAME} {PROVIDER_RESOURCE_ID}")
      terraformData.append(f"resource \"{TERRAFORM_RESOURCE_TYPE}\" \"{TF_RESOURCE_NAME}\" {{}}\n")
  WriteArrayToFile(TERRAFORM_IMPORT_SCRIPT, importData)
  WriteArrayToFile(TERRAFORM_SKELETON_TF_FILE, terraformData)

"""
  Function: CreateAwsImportFiles

  Description: Creates a script with "terraform import <resource> <id>" command syntaxt to import the required resources to 
    the Terraform state file and creates also a skeleton terraform (.tf) file with the resources that will be
    imported.

  TODO
    - move JSON_DATA_FILE to cmd argument, 
    - Changed the code to allow multiple providers. Swiched to a more robust lib to handle json dot paths.
"""
def CreateAwsImportFiles():
  # data = LoadJsonFile(JSON_DATA_FILE)
  data = LoadJsonFile("data/provider_aws_ec2.json")
  # data = LoadJsonFile("data/provider_aws_efs.json")
  importData=[]
  terraformData=[]
  for resource in data[PROVIDER_RESOURCE_ROOT]:
    if re.search(r":", PROVIDER_RESOURCE_NAME_KEY):
      [ jsonPath, keyName ] = PROVIDER_RESOURCE_NAME_KEY.split(":")
      TF_RESOURCE_NAME=GetValueFromKey(GetResourceValueByKeyPath(resource, f"$..{jsonPath}" ), keyName)
    else:
      TF_RESOURCE_NAME=GetResourceValueByKeyPath(resource, f"$..{PROVIDER_RESOURCE_NAME_KEY}")
    PROVIDER_RESOURCE_ID=GetResourceValueByKeyPath(resource, f"$..{PROVIDER_RESOURCE_ID_KEY}")
    importData.append(f"terraform import {TERRAFORM_RESOURCE_TYPE}.{TF_RESOURCE_NAME} {PROVIDER_RESOURCE_ID}")
    terraformData.append(f"resource \"{TERRAFORM_RESOURCE_TYPE}\" \"{TF_RESOURCE_NAME}\" {{}}\n")
  WriteArrayToFile(TERRAFORM_IMPORT_SCRIPT, importData)
  WriteArrayToFile(TERRAFORM_SKELETON_TF_FILE, terraformData)

def GetValueFromKey(kvpData, keyName):
  for keyvp in kvpData:
    if keyvp['Key'] == keyName:
      return keyvp['Value']
  return False

def GetResourceValueByKeyPath(jsonObject, pathToKey):
  jsonPathParser = parse(pathToKey)
  matches = jsonPathParser.find(jsonObject)
  return matches[0].value

"""
  Function: FindResourceInstancesFromTfstate

  Description: Searches a Terraform state file (terraform.tfstate) for a resoruce instance with the
    specified 'name' and 'type'. Both 'name' and 'type' must be found otherwise it will return false.

  Parameters:
    - tfState: The contents of the Terraform state file
    - type: The type of the resource to find
    - name: The name of the resource to find

  Return: The attributes of the resource, or FALSE if not found.
"""
def FindResourceInstancesFromTfstate(tfState, type, name):
  for resource in tfState['resources']:
    if resource['type'] == type and resource['name'] == name:
      # instances[0] is a terrible assumption
      return resource['instances'][0]['attributes']
  return False

"""
  Function: CastValueToTerraformType

  Description: Converts a value from a Dict to the correct format in a Terraform file.
    For example will convert Python False to false and None to null.

  Parameters:
    - value: The value to convert from

  Return: The value as a valid value in Terraform.
"""
def CastValueToTerraformType(value):
  if value == None: return "null"
  if isinstance(value, bool): return f"{str(value).lower()}"
  if isinstance(value, int): return int(value)
  return value

"""
  Function: ImportFromTfState

  Description: Imports the selected resources and fields defined in the TERRAFORM_MAPPINGS_FILE, with
    data from Terraform state file into the TERRAFORM_RESOURCE_TF_FILE.
"""
def ImportFromTfState():
  terraformStateData = LoadJsonFile(TERRAFORM_STATE_FILE)
  importData = LoadTextFile(TERRAFORM_SKELETON_TF_FILE)
  mappings = LoadJsonFile(TERRAFORM_MAPPING_FILE)
  terraformResourceData = ""
  tfstateJsonData = {}
  for line in importData.split("\n"):
    if line != "":
      [ a, resourceType, resourceName, d] = line.replace('"',"").split()
      tfstateInstanceAttributes = FindResourceInstancesFromTfstate(terraformStateData, resourceType, resourceName)
      terraformResourceData = f'{terraformResourceData}resource "{resourceType}" "{resourceName}" '
      if tfstateInstanceAttributes:
        for key in mappings[resourceType]:
            tfstateJsonData[key] = CastValueToTerraformType(tfstateInstanceAttributes[key])
        terraformResourceData = f'{terraformResourceData}{json.dumps(tfstateJsonData, cls=TerraformEncoder)}'
      terraformResourceData = f'{terraformResourceData} \n\n'

  WriteTextToFile(TERRAFORM_RESOURCE_TF_FILE, terraformResourceData)

"""
  Function: LoadConfig

  Description: Loads the configuration from 'settings.cgf'.
"""
def LoadConfig(provider):
  global JSON_DATA_FILE
  global TERRAFORM_IMPORT_SCRIPT
  global TERRAFORM_SKELETON_TF_FILE
  global TERRAFORM_RESOURCE_TYPE
  global TERRAFORM_STATE_FILE
  global TERRAFORM_MAPPING_FILE
  global PROVIDER_RESOURCE_ROOT
  global PROVIDER_RESOURCE_TYPE
  global PROVIDER_RESOURCE_ID_KEY
  global PROVIDER_RESOURCE_NAME_KEY

  cfg = configparser.RawConfigParser()
  cfg.optionxform = lambda option: option # Prevent config parser from changing the CASE of variable names
  cfg.read('settings.cfg')
  # Common settings
  settings=dict(cfg.items("Settings"))
  for setting in settings:
    settings[setting]=settings[setting].split("#",1)[0].strip() # To get rid of inline comments
  globals().update(settings)  # Make them availible globally
  # Define settings from the provider settings section
  settings=dict(cfg.items(provider))
  for setting in settings:
    settings[setting]=settings[setting].split("#",1)[0].strip() # To get rid of inline comments
  globals().update(settings)  # Make them availible globally

"""
  Function: main

  Description: Loads the settings and checks the command line arguments. Deciding what functions to call
    based on the arguments.

"""
def main():
  parser = argparse.ArgumentParser(description='Import existing provider resources to Terraform')
  parser.add_argument("-p", "--provider", choices=["aws", "azure", "gcp", "digitalocean"], required=True, help="")
  group = parser.add_mutually_exclusive_group()
  group.add_argument("-c", "--create", action="store_true", help="Create 'terraform import' script and file for resources")
  group.add_argument("-m", "--merge", action="store_true", help=f"Merge properties from terraform state file to '{TERRAFORM_RESOURCE_TF_FILE}'")

  args = parser.parse_args()

  if args.provider:
    LoadConfig(args.provider)
  if args.create:
    match args.provider:
      case "aws":
        CreateAwsImportFiles()
      case "azure":
        return CreateAzureImportFiles()
  elif args.merge:
    ImportFromTfState()
  else:
    args = parser.parse_args(['-h'])

# Python import guard
if __name__ == "__main__":
  main()
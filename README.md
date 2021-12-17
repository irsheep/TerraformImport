# TerraformImport
This script will assist in creating the required ```terraform import``` commands and Terraform file to import existing resources from a cloud provider to a new or existing Terraform configuration. At the moment the script won't use any References to Named Values.

# Usage
Assuming everything is in place, the following would create a file named 'resources.tf' with the imported resources to Terraform HCL configuration.

```bash
$ ./import.py -p aws -c
$ terraform import "aws_compute_instance.i-deadbeef" "my_machine"
$ ./import.py -p aws -m
```

See below for a more detailed description of the process.

## Get data from provider
The first step is to get a JSON representation of the cloud objects to import. This will vary from Cloud provider to Cloud provider, as example we will use Aws, Azure, Digital Ocean and Google to import existing "_virtual machines_".

```bash
# Aws
$ aws ec2 describe-instances
# Azure
$ az vm list
# Digital Ocean
$ doctl compute droplet list -o json
# Google
$ gcloud compute instances list --format=json
```

## Prepare files
The script uses a few files for configuration to read and store data, the next step is to change the settings on some of the files to match your requirements.

### settings.cfg
A sample file, **settings.sample.cfg**, with default settings for some Cloud providers is provided with the script, copy this file as **settings.cfg** and edit to match your local environment.
The following example creates a section named **gcp** (for Google Cloud Platform) to import _virtual machines_.

```ini
[gcp]
# Terraform provider resource type
TERRAFORM_RESOURCE_TYPE = google_compute_instance
# The name of the key where the resource id is stored by the provider
PROVIDER_RESOURCE_ID_KEY = id
# Dot path to the resource name
PROVIDER_RESOURCE_NAME_KEY = name
```

### mapping.json
The mapping file is used to define what properties are imported to the Terraform resources. Reference to the Terraform documentation to know what properties are **required** for each resource type, and what properties can be used. This script will import any matching property, even if Terraform doesn't support that property, which will cause errors when running terraform plan or apply.

```json
{
    "aws_instance": [
        "ami",
        "instance_type",
        "tags",
        "cpu_core_count",
        "root_block_device",
        "security_groups"
    ]
}
```

## generate files
Running the script with the create switch (-c or --create), will cause the script to create the import script and a skeleton Terraform file. Resources that already exist in the **terraform.tfstate** file will be skipped, to change this behaviour and include all resources use the **--include-all** command line argument.

```
$ python import.py -p <cfg_section> -c
```

The following is an example of the two files created.

_import.sh_
```bash
$ terraform import aws_instance.machine1 i-deadbeef
```
_skeleton.tf_
```terraform
resource "aws_instance" "machine1" {}
```

## Run terraform import
Before running any of the ```terraform import``` commands make a backup of your **terraform.tfstate** file.
Either run the ```import.sh``` script or edit it and run each line manually.

```bash
$ terraform import aws_instance.machine1 i-deadbeef
```

## Import resources
Once the required resources have been imported to the Terraform state file, run the script again with the merge (-m or --merge) switch to generate a new terraform file _TERRAFORM_RESOURCE_TF_FILE_ with the resources defined in _TERRAFORM_SKELETON_TF_FILE_ file and properties defined in _TERRAFORM_MAPPING_FILE_.

```
$ python import.py -p <cfg_section> -m
```
WARNING: The script will overwrite the contents of _TERRAFORM_RESOURCE_TF_FILE_, every time it runs.

# Configuration settings

## Application data files
These settings mainly handle the location of files used by the script to read and store data.

- JSON_DATA_FILE: Path and name to the location of the file with the JSON data exported from the cloud provider
- TERRAFORM_STATE_FILE: Path and name to existing Terraform state file (terraform.tfstate). Although this script does not modify the file directly, the Terraform state file will be modified when ```terraform import``` commands are run by the user.
- TERRAFORM_IMPORT_SCRIPT: Bash script with the ```terraform import``` commands to execute.
- TERRAFORM_SKELETON_TF_FILE: A skeleton file with the minimum HCL syntax to act as placeholder
- TERRAFORM_RESOURCE_TF_FILE: Terraform file which will contain the imported resources
- TERRAFORM_MAPPING_FILE: JSON file to map Terraform resources and what properties to import into the resource
- TERRAFORM_RESOURCE_TYPE: The name of the resource as per Terraform documentation

**ATTENTION:** Backup your terraform state file, before running the ```terraform import``` commands.

## Provider resource identifiers
The following two settings define the name of the keys, used to select the resource id and name.

- PROVIDER_RESOURCE_ID_KEY: The name of the key in the JSON_DATA_FILE that contains the 'id' of the resource
- PROVIDER_RESOURCE_NAME_KEY: The name of the key in the JSON_DATA_FILE that contains the 'name' of the resource. For keys that have a list of _key-value-pairs_ as its value, the format **A:B** can be used to select a value, from the _key-value-pair_ list where **B** is the value of the **Key** and **A** is the name of the key where the _key-value-pair_ list is stored.

### _EXAMPLE_:
The following would use the key named **FileSystemId** as the **id** of the resource and the value of the key named **Name** of a _key-value-pair_ list.
```ini
# The name of the key where the resource id is stored by the provider
PROVIDER_RESOURCE_ID_KEY = FileSystemId
# Dot path to the resource name
PROVIDER_RESOURCE_NAME_KEY = Tags:Name
```

```json
           (...)
            "CreationToken": "quickCreated-a-b-c-d",
            "FileSystemId": "fs-deadbeef",
            "FileSystemArn": "arn:aws:elasticfilesystem:eu-west-1:123:file-system/fs-deadbeef",
            "CreationTime": "1970T00:00:00+00:00",
            "AvailabilityZoneId": "zone-a",
            "Tags": [{
                    "Key": "Name",
                    "Value": "DiskA"
                },
                {
                    "Key": "aws:elasticfilesystem:default-backup",
                    "Value": "enabled"
                }
            ]
        }
```        

## Provider resource filters
These settings allow the script to import only resources that match the filter settings.

- PROVIDER_RESOURCE_FILTER_KEY: Name of the key.
- PROVIDER_RESOURCE_FILTER_VALUE: String to search within the key value/

### _EXAMPLE_:
In **Azure Backup Center** you can have a mix of _virtual machines_, _storage shares_, and other resources in a single vault.

```json
    (...)
    {
        "eTag": null,
        "id": "/subscriptions/aaa-bbb-ccc-ddd/resourceGroups/MyResourceGroup/providers/Microsoft.RecoveryServices/vaults/MyVault/backupFabrics/Azure/protectionContainers/IaasVMContainer;iaasvmcontainerv2;MyResourceGroup;MyVm1/protectedItems/VM;iaasvmcontainerv2;MyResourceGroup;MyVm1",
        "name": "VM;iaasvmcontainerv2;MyResourceGroup;MyVm1",
        "type": "Microsoft.RecoveryServices/vaults/backupFabrics/protectionContainers/protectedItems"
    },
    {
        "eTag": null,
        "id": "/subscriptions/aaa-bbb-ccc-ddd/resourceGroups/MyResourceGroup/providers/Microsoft.RecoveryServices/vaults/MyVault/backupFabrics/Azure/protectionContainers/StorageContainer;Storage;MyResourceGroup;MyStorageAccount/protectedItems/AzureFileShare;MyShare",
        "name": "AzureFileShare;MyShare",
        "type": "Microsoft.RecoveryServices/vaults/backupFabrics/protectionContainers/protectedItems"
    },
    (...)
```

Using the settings below, the script would only import resources with **AzureFileShare** in its **name**, as the filter uses a _wildcard_ comparison.

```ini
PROVIDER_RESOURCE_FILTER_KEY = name
PROVIDER_RESOURCE_FILTER_VALUE = AzureFileShare
```

Resulting in the following Terraform configuration.
```terraform
resource "azurerm_backup_protected_file_share" "MyShare" {
  resource_group_name = "MyResourceGroup"
  recovery_vault_name = "MyVault"
  source_storage_account_id = "/subscriptions/aaa-bbb-ccc-ddd/resourceGroups/MyResourceGroup/providers/Microsoft.Storage/storageAccounts/MyStorageAccount"
  source_file_share_name = "MyShare"
  backup_policy_id = "/subscriptions/aaa-bbb-ccc-ddd/resourceGroups/MyResourceGroup/providers/Microsoft.RecoveryServices/vaults/MyVault/backupPolicies/MyPolicy
} 
```

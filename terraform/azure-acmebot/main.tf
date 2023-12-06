terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "Terraform"
    storage_account_name = "aktfstate"
    container_name       = "tfstate"
    key                  = "keyvault-acmebot.tfstate"
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}

variable "resourceGroupName" {
  default  = "ssl-certs"
  nullable = false
  type     = string
}

variable "keyVaultName" {
  default  = "ak-certs-vault"
  nullable = false
  type     = string
}

data "azurerm_client_config" "current" { }

data "azurerm_resource_group" "rg" {
  name = var.resourceGroupName
}

data "azurerm_key_vault" "vault" {
  name                = var.keyVaultName
  resource_group_name = var.resourceGroupName
}

module "keyvault_acmebot" {
  source  = "shibayan/keyvault-acmebot/azurerm"
  version = "~> 3.0"

  app_base_name         = "acmebot-azure"
  resource_group_name   = data.azurerm_resource_group.rg.name
  location              = data.azurerm_resource_group.rg.location
  mail_address          = "andy@mechanus.pro"
  vault_uri             = data.azurerm_key_vault.vault.vault_uri

  azure_dns = {
    subscription_id = data.azurerm_client_config.current.subscription_id
  }
}

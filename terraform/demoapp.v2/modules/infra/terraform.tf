terraform {
  required_providers {
    azapi = {
      source = "azure/azapi"
      version = ">=1.10.0"
    }

    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }

    random = {
      source = "hashicorp/random"
      version = ">=3.6.0"
    }
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}

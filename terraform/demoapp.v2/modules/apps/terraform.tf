terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }

    azapi = {
      source  = "Azure/azapi"
      version = ">=1.10.0"
    }

    random = {
      source = "hashicorp/random"
      version = ">=3.6.0"
    }

    time = {
      source  = "hashicorp/time"
      version = ">=0.9.2"
    }
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}



terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }

    azuread = {
      source  = "hashicorp/azuread"
      version = ">=2.46.0"
    }

    azapi = {
      source  = "Azure/azapi"
      version = ">=1.10.0"
    }

    time = {
      source  = "hashicorp/time"
      version = ">=0.9.2"
    }
  }

  backend "azurerm" {
    resource_group_name  = "Terraform"
    storage_account_name = "aktfstate"
    container_name       = "tfstate"
    key                  = "container-demoapp.tfstate"
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}

locals {
  fullImageName = "${data.azurerm_container_registry.appRegistry.login_server}/${var.containerImage}:${var.containerTag}"
}

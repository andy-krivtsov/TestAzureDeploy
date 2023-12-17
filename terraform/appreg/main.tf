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
    key                  = "test-app-reg.tfstate"
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}


resource "azuread_application" "testapp" {
  display_name     = var.azureadAppDisplayName
  sign_in_audience = "AzureADMyOrg"

  description = "Test application registration created by Terraform"

  notes = "Notes: Application created by Terraform"

  prevent_duplicate_names = true

  feature_tags {
    enterprise = true
  }

  required_resource_access {
    resource_app_id = "00000003-0000-0000-c000-000000000000" # Microsoft Graph

    resource_access {
      id   = "df021288-bdef-4463-88db-98f22de89214" # User.Read.All
      type = "Role"
    }
  }

  web {
    homepage_url  = var.homepageUrl
    logout_url    = var.logoutUrl
    redirect_uris = var.redirectUris

    implicit_grant {
      access_token_issuance_enabled = true
      id_token_issuance_enabled     = true
    }
  }
}

resource "azuread_application_password" "testapp" {
  application_id = azuread_application.testapp.id
  display_name = "testapp_auto_secret"
  end_date_relative = "8760h"
}

resource "azuread_service_principal" "testapp" {
  client_id                    = azuread_application.testapp.client_id
  feature_tags {
    enterprise = true
  }
}

output "client_id" {
  value = azuread_application.testapp.client_id
}

output "client_secret" {
  value = azuread_application_password.testapp.value
  sensitive = true
}

output "object_id" {
  value = azuread_application.testapp.object_id
}

output "service_principal_object_id" {
  value = azuread_service_principal.testapp.object_id
}

output "service_principal_client_id" {
  value = azuread_service_principal.testapp.client_id
}

output "service_principal_id" {
  value = azuread_service_principal.testapp.id
}

output "service_principal_tenant_id" {
  value = azuread_service_principal.testapp.application_tenant_id
}






resource "azurerm_user_assigned_identity" "conapp" {
  name                = "${var.namePrefix}-identity"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
}

resource "azurerm_role_assignment" "registry_pull" {
  scope                = data.azurerm_container_registry.appRegistry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.conapp.principal_id
}

resource "azuread_application" "azuread_app" {
  display_name     = var.azureadAppRegistration["displayName"]
  sign_in_audience = "AzureADMyOrg"

  description = var.azureadAppRegistration["description"]

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
    homepage_url  = var.azureadAppRegistration["homepageUrl"]
    logout_url    = var.azureadAppRegistration["logoutUrl"]
    redirect_uris = var.azureadAppRegistration["redirectUris"]

    implicit_grant {
      access_token_issuance_enabled = true
      id_token_issuance_enabled     = true
    }
  }
}

resource "azuread_application_password" "azuread_app" {
  application_id    = azuread_application.azuread_app.id
  display_name      = "Terraform created secret"
  end_date_relative = "8760h"
}

resource "azuread_service_principal" "azuread_app" {
  client_id = azuread_application.azuread_app.client_id
  feature_tags {
    enterprise = true
  }
}

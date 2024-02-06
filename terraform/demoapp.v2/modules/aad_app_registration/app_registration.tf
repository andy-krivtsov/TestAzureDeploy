resource "azuread_application" "azuread_app" {
  display_name            = var.display_name
  sign_in_audience        = "AzureADMyOrg"
  description             = var.description
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
    homepage_url  = var.homepage_url
    logout_url    = var.logout_url
    redirect_uris = var.redirect_uris

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

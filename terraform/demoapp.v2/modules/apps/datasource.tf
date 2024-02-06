data "azurerm_container_app_environment" "app_env" {
  name                = var.con_app_env
  resource_group_name = var.con_app_env_rg
}

data "azurerm_container_app_environment_certificate" "app_env_cert" {
  name                         = var.con_app_env_cert
  container_app_environment_id = data.azurerm_container_app_environment.appenv.id
}

data "azapi_resource" "conapp_env_api" {
  resource_id = azurerm_container_app_environment.conapp_env.id
  type        = "Microsoft.App/managedEnvironments@2022-11-01-preview"

  response_export_values = ["properties.customDomainConfiguration.customDomainVerificationId"]
}

data "azurerm_user_assigned_identity" "con_app" {
  name                = var.con_app_user_identity
  resource_group_name = con_app_env_rg
}

data "azurerm_container_registry" "app_registry" {
  name                = var.acr_registry
  resource_group_name = var.acr_registry_rg
}

data "azurerm_key_vault" "secrets" {
  name                = var.keyvault
  resource_group_name = var.keyvault_rg
}

data "azurerm_key_vault_secret" "secrets" {
  key_vault_id = data.azurerm_key_vault.secrets.id
  for_each     = toset(var.keyvault_secrets)
  name         = "${var.keyvault_prefix}${each.key}"
}

locals {
  domain_verification_id = jsondecode(data.azapi_resource.conapp_env_api.output).properties.customDomainConfiguration.customDomainVerificationId
  full_image_name        = "${data.azurerm_container_registry.app_registry.login_server}/${var.app_image}:${var.app_tag}"

  app_secrets = { for k, v in data.azurerm_key_vault_secret.secrets : k => v.value }
}

resource "random_id" "random_suffix" {
  keepers = {
    time = timestamp()
  }
  byte_length = 4
}

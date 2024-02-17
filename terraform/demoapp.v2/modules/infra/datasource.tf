data "azurerm_client_config" "current" {
}

data "azurerm_resource_group" "rg" {
  name = var.resource_group
}

data "azurerm_key_vault" "cert_vault" {
  name                = var.cert_keyvault
  resource_group_name = var.cert_keyvault_rg
}

data "azurerm_key_vault_certificate" "app_cert" {
  name         = var.cert_keyvault_key
  key_vault_id = data.azurerm_key_vault.cert_vault.id
}

data "azurerm_key_vault_secret" "app_cert_secret" {
  name         = element(reverse(split("/", data.azurerm_key_vault_certificate.app_cert.secret_id)), 1)
  key_vault_id = data.azurerm_key_vault.cert_vault.id
}

data "azurerm_container_registry" "app_registry" {
  name                = var.acr_registry
  resource_group_name = var.acr_registry_rg
}

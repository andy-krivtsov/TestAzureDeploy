data "azurerm_client_config" "current" {
}

data "azurerm_key_vault" "certVault" {
  name                = var.certKeyVaultName
  resource_group_name = var.certKeyVaultRG
}

data "azurerm_key_vault_certificate" "keyVaultAppCert" {
  name         = var.certKeyVaultKey
  key_vault_id = data.azurerm_key_vault.certVault.id
}

data "azurerm_key_vault_secret" "appCertSecret" {
  name         = element(reverse(split("/", data.azurerm_key_vault_certificate.keyVaultAppCert.secret_id)), 1)
  key_vault_id = data.azurerm_key_vault.certVault.id
}

data "azurerm_resource_group" "rg" {
  name = var.resourceGroupName
}

resource "random_id" "deploy_id" {
  keepers = {
    rg_name = var.resourceGroupName
  }
  byte_length = 4
}

data "azurerm_container_registry" "appRegistry" {
  name                = var.registry
  resource_group_name = var.registryRG
}

resource "random_id" "random_suffix" {
  keepers = {
    time = "${timestamp()}"
  }
  byte_length = 4
}

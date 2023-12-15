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

data "azuread_service_principal" "appServicePrincipal" {
  client_id = data.azurerm_key_vault_secret.vaultSecrets["auth-client-id"].value
}

data "azurerm_user_assigned_identity" "appIdentity" {
  name                = var.identityName
  resource_group_name = data.azurerm_resource_group.rg.name
}

resource "random_id" "deploy_id" {
  keepers = {
    rg_name = var.resourceGroupName
  }
  byte_length = 4
}

data "azurerm_key_vault" "secretsVault" {
  name                = var.secretsKeyVaultName
  resource_group_name = var.secretsKeyVaultRG
}

# Vault secrets by app secret name (ex. vaultSecrets['auth_client_id'])
data "azurerm_key_vault_secret" "vaultSecrets" {
  for_each     = var.appKeyvaultSecrets
  name         = each.value
  key_vault_id = data.azurerm_key_vault.secretsVault.id
}

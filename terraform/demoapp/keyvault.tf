resource "azurerm_key_vault" "secretsVault" {
  name                            = "${var.namePrefix}-vault-${random_id.deploy_id.hex}"
  location                        = data.azurerm_resource_group.rg.location
  resource_group_name             = data.azurerm_resource_group.rg.name
  enabled_for_disk_encryption     = true
  tenant_id                       = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days      = 7
  purge_protection_enabled        = false
  enabled_for_deployment          = true
  enabled_for_template_deployment = true
  enable_rbac_authorization       = true
  sku_name                        = "standard"
}

resource "azurerm_role_assignment" "secretsVaultRole" {
  scope                = azurerm_key_vault.secretsVault.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_secret" "clientId" {
  name         = "${var.namePrefix}-auth-client-id"
  value        = azuread_application.azuread_app.client_id
  key_vault_id = azurerm_key_vault.secretsVault.id

  depends_on = [ azurerm_role_assignment.secretsVaultRole ]
}

resource "azurerm_key_vault_secret" "clientSecret" {
  name         = "${var.namePrefix}-auth-client-secret"
  value        = azuread_application_password.azuread_app.value
  key_vault_id = azurerm_key_vault.secretsVault.id

  depends_on = [ azurerm_role_assignment.secretsVaultRole ]
}

resource "azurerm_key_vault_secret" "tenantId" {
  name         = "${var.namePrefix}-auth-tenant-id"
  value        = azuread_service_principal.azuread_app.application_tenant_id
  key_vault_id = azurerm_key_vault.secretsVault.id

  depends_on = [ azurerm_role_assignment.secretsVaultRole ]
}

resource "random_password" "sessionKey" {
  length           = 21
  special          = true
}

resource "azurerm_key_vault_secret" "sessionKey" {
  name         = "${var.namePrefix}-auth-session-key"
  value        = random_password.sessionKey.result
  key_vault_id = azurerm_key_vault.secretsVault.id

  depends_on = [ azurerm_role_assignment.secretsVaultRole ]
}
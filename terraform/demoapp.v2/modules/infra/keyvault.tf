resource "azurerm_key_vault" "secrets_vault" {
  name                            = "${var.name_prefix}-vault-${random_id.deploy_id.hex}"
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

resource "azurerm_role_assignment" "secrets_vault_role" {
  scope                = azurerm_key_vault.secrets_vault.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_secret" "clientId" {
  name         = "${var.name_prefix}-auth-client-id"
  value        = var.app_client_id
  key_vault_id = azurerm_key_vault.secrets_vault.id

  depends_on   = [ azurerm_role_assignment.secrets_vault_role ]
}

resource "azurerm_key_vault_secret" "client_secret" {
  name         = "${var.name_prefix}-auth-client-secret"
  value        = var.app_client_secret
  key_vault_id = azurerm_key_vault.secrets_vault.id

  depends_on   = [ azurerm_role_assignment.secrets_vault_role ]
}

resource "azurerm_key_vault_secret" "tenant_id" {
  name         = "${var.name_prefix}-auth-tenant-id"
  value        = var.app_tenant_id
  key_vault_id = azurerm_key_vault.secrets_vault.id

  depends_on   = [ azurerm_role_assignment.secrets_vault_role ]
}

resource "random_password" "session_key" {
  length           = 21
  special          = true
}

resource "azurerm_key_vault_secret" "session_key" {
  name         = "${var.name_prefix}-auth-session-key"
  value        = random_password.session_key.result
  key_vault_id = azurerm_key_vault.secrets_vault.id

  depends_on   = [ azurerm_role_assignment.secrets_vault_role ]
}
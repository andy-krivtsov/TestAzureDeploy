# Container environment and support services
resource "azurerm_container_app_environment" "conapp_env" {
  name                       = var.con_app_env
  resource_group_name        = data.azurerm_resource_group.rg.name
  location                   = data.azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}

resource "azurerm_container_app_environment_certificate" "app_cert" {
  name                         = var.con_app_env_cert
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  certificate_blob_base64      = data.azurerm_key_vault_secret.app_cert_secret.value
  certificate_password         = ""
}

resource "azurerm_container_app_environment_storage" "conapp_env_stor" {
  name                         = "azurefiles"
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  account_name                 = azurerm_storage_account.stor.name
  share_name                   = azurerm_storage_share.stor_share.name
  access_key                   = azurerm_storage_account.stor.primary_access_key
  access_mode                  = "ReadWrite"
}

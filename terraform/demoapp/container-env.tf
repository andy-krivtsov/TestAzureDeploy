# Container environment and support services
resource "azurerm_storage_account" "stor" {
  name                     = "${var.storageAccountPrefix}${random_id.deploy_id.hex}"
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  access_tier              = "Hot"
}

resource "azurerm_storage_share" "stor_share" {
  name                 = "containerapps"
  storage_account_name = azurerm_storage_account.stor.name
  quota                = 10
}

resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.logWorkspacePrefix}${random_id.deploy_id.hex}"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "conapp_env" {
  name                       = var.environmentName
  resource_group_name        = data.azurerm_resource_group.rg.name
  location                   = data.azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}

resource "azurerm_container_app_environment_certificate" "appCert" {
  name                         = var.certKeyVaultKey
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  certificate_blob_base64      = data.azurerm_key_vault_secret.appCertSecret.value
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

data "azapi_resource" "conapp_env_api" {
  resource_id = azurerm_container_app_environment.conapp_env.id
  type        = "Microsoft.App/managedEnvironments@2022-11-01-preview"

  response_export_values = ["properties.customDomainConfiguration.customDomainVerificationId"]
}

resource "azurerm_storage_account" "stor" {
  name                     = "${var.storage_account}${var.name_suffix}"
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  access_tier              = "Hot"
}

resource "azurerm_storage_container" "stor_container" {
  name                  = var.storage_container
  storage_account_name  = azurerm_storage_account.stor.name
  container_access_type = "private"
}

resource "azurerm_role_assignment" "stor_writer" {
  scope                = azurerm_storage_account.stor.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.app_service_principal_id
}

resource "azurerm_storage_share" "stor_share" {
  name                 = "containerapps"
  storage_account_name = azurerm_storage_account.stor.name
  quota                = 10
}

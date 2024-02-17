resource "azurerm_user_assigned_identity" "conapp" {
  name                = var.con_app_env_identity
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
}

resource "azurerm_role_assignment" "registry_pull" {
  scope                = data.azurerm_container_registry.app_registry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.conapp.principal_id
}
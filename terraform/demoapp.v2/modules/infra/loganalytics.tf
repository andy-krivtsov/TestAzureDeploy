resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.con_app_env_log}-${var.name_suffix}"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

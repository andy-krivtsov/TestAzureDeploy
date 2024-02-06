resource "azurerm_application_insights" "appinsights" {
  name                =  "${var.name_prefix}-appinsights-${random_id.deploy_id.hex}"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.logs.id
  application_type    = "other"
  retention_in_days   = 30
  disable_ip_masking  = true
}

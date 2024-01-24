resource "azurerm_web_pubsub" "pubsub" {
  name                = "${var.namePrefix}-pubsub-${random_id.deploy_id.hex}"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name

  sku      = "Free_F1"
  capacity = 1

  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  live_trace {
    enabled                   = true
    messaging_logs_enabled    = true
    connectivity_logs_enabled = false
  }
}

resource "azurerm_web_pubsub_hub" "front" {
  name                          = "front"
  web_pubsub_id                 = azurerm_web_pubsub.pubsub.id
  anonymous_connections_enabled = false
}


resource "azurerm_web_pubsub" "pubsub" {
  name                = "${var.web_pubsub}-${var.name_suffix}"
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
    connectivity_logs_enabled = true
  }
}

resource "azurerm_web_pubsub_hub" "front" {
  name                          = var.web_pubsub_front_hub
  web_pubsub_id                 = azurerm_web_pubsub.pubsub.id
  anonymous_connections_enabled = false

  event_handler {
    url_template       = var.pubsub_handlers.front
    user_event_pattern = "*"
    system_events      = ["connect","connected","disconnected"]
  }
}

resource "azurerm_role_assignment" "webpubsub_owner" {
  scope                = azurerm_web_pubsub.pubsub.id
  role_definition_name = "Web PubSub Service Owner"
  principal_id         = var.app_service_principal_id
}


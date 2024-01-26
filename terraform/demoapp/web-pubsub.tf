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
    connectivity_logs_enabled = true
  }
}

resource "azurerm_web_pubsub_hub" "front" {
  name                          = "front"
  web_pubsub_id                 = azurerm_web_pubsub.pubsub.id
  anonymous_connections_enabled = false

  dynamic "event_handler" {
    for_each = var.localDev ? [] : [1]
    content {
      url_template       = "https://front${var.hostnameSuffix}.${var.customDnsZone}/notifications/events"
      user_event_pattern = "*"
      system_events      = ["connect","connected","disconnected"]
    }
  }

  dynamic "event_handler" {
    for_each = var.localDev ? [1] : []
    content {
      url_template       = "tunnel:///notifications/events"
      user_event_pattern = "*"
      system_events      = ["connect","connected","disconnected"]
    }
  }
}

resource "azurerm_role_assignment" "webpubsub_owner" {
  scope                = azurerm_web_pubsub.pubsub.id
  role_definition_name = "Web PubSub Service Owner"
  principal_id         = azuread_service_principal.azuread_app.object_id
}


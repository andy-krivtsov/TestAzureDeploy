# Service bus
resource "azurerm_servicebus_namespace" "busNamespace" {
  name                = "${var.namePrefix}-namespace-${random_id.deploy_id.hex}"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "Standard"
}

resource "azurerm_servicebus_topic" "orders_topic" {
  name                = "${var.namePrefix}-orders-topic"
  namespace_id        = azurerm_servicebus_namespace.busNamespace.id
  default_message_ttl = "PT8H"
}

resource "azurerm_servicebus_topic" "status_topic" {
  name                = "${var.namePrefix}-status-topic"
  namespace_id        = azurerm_servicebus_namespace.busNamespace.id
  default_message_ttl = "PT8H"
}

resource "azurerm_servicebus_subscription" "back_orders_sub" {
  name               =  "${var.namePrefix}-back-orders-sub"
  topic_id           = azurerm_servicebus_topic.orders_topic.id
  max_delivery_count = 1
}

resource "azurerm_servicebus_subscription" "front_status_sub" {
  name               =  "${var.namePrefix}-front-status-sub"
  topic_id           = azurerm_servicebus_topic.status_topic.id
  max_delivery_count = 1
}

resource "azurerm_role_assignment" "orders_topic_admin" {
  scope                = azurerm_servicebus_topic.orders_topic.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = azuread_service_principal.azuread_app.object_id
}

resource "azurerm_role_assignment" "status_topic_admin" {
  scope                = azurerm_servicebus_topic.status_topic.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = azuread_service_principal.azuread_app.object_id
}

resource "azurerm_role_assignment" "back_sub_admin" {
  scope                = azurerm_servicebus_subscription.back_orders_sub.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = azuread_service_principal.azuread_app.object_id
}

resource "azurerm_role_assignment" "front_sub_admin" {
  scope                = azurerm_servicebus_subscription.front_status_sub.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = azuread_service_principal.azuread_app.object_id
}

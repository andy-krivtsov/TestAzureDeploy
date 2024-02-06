# Service bus
resource "azurerm_servicebus_namespace" "app_ns" {
  name                = "${var.name_prefix}-namespace-${random_id.deploy_id.hex}"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "Standard"
}

resource "azurerm_servicebus_topic" "orders_topic" {
  name                = "${var.name_prefix}-orders-topic"
  namespace_id        = azurerm_servicebus_namespace.app_ns.id
  default_message_ttl = "PT8H"
}

resource "azurerm_servicebus_topic" "status_topic" {
  name                = "${var.name_prefix}-status-topic"
  namespace_id        = azurerm_servicebus_namespace.app_ns.id
  default_message_ttl = "PT8H"
}

resource "azurerm_servicebus_subscription" "back_orders_sub" {
  name               =  "${var.name_prefix}-back-orders-sub"
  topic_id           = azurerm_servicebus_topic.orders_topic.id
  max_delivery_count = 1
}

resource "azurerm_servicebus_subscription" "front_status_sub" {
  name               =  "${var.name_prefix}-front-status-sub"
  topic_id           = azurerm_servicebus_topic.status_topic.id
  max_delivery_count = 1
}

resource "azurerm_role_assignment" "orders_topic_admin" {
  scope                = azurerm_servicebus_topic.orders_topic.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = var.app_service_principal_id
}

resource "azurerm_role_assignment" "status_topic_admin" {
  scope                = azurerm_servicebus_topic.status_topic.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = var.app_service_principal_id
}

resource "azurerm_role_assignment" "back_sub_admin" {
  scope                = azurerm_servicebus_subscription.back_orders_sub.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = var.app_service_principal_id
}

resource "azurerm_role_assignment" "front_sub_admin" {
  scope                = azurerm_servicebus_subscription.front_status_sub.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = var.app_service_principal_id
}

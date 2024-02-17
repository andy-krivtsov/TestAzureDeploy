variable "con_app_env" {
  type = string
}

variable "con_app_env_log" {
  type = string
}

variable "app_insight" {
  type = string
}

variable "db_account" {
  type = string
}

variable "db_database" {
  type = string
}

variable "db_orders_container" {
  type = string
}

variable "db_processing_container" {
  type = string
}

variable "con_app_env_identity" {
  type = string
}

variable "con_app_env_cert" {
  type = string
}

variable "keyvault" {
  type = string
}

variable "keyvault_prefix" {
  type = string
}

variable "servicebus_namespace" {
  type = string
}

variable "servicebus_orders_topic" {
  type = string
}

variable "servicebus_status_topic" {
  type = string
}

variable "servicebus_front_status_sub" {
  type = string
}

variable "servicebus_back_orders_sub" {
  type = string
}

variable "storage_account" {
  type = string
}

variable "storage_container" {
  type = string
}

variable "web_pubsub" {
  type = string
}

variable "web_pubsub_front_hub" {
  type = string
}

variable "name_suffix" {
  type = string
}

variable "pubsub_handlers" {
  type  = map(string)
  # default = {
  #   "front" = "tunnel:///notifications/events"
  # }
}

variable "resource_group" {
  type     = string
# default  = "AzureLearnDev"
}

variable "acr_registry" {
  type     = string
#  default  = "akazureregistry"
}

variable "acr_registry_rg" {
  type     = string
#  default  = "AzureLearn"
}

variable "cert_keyvault" {
  type     = string
#  default  = "ak-certs-vault"
}

variable "cert_keyvault_rg" {
  type     = string
#  default  = "ssl-certs"
}

variable "cert_keyvault_key" {
  type     = string
#  default  = "wildcard-az-mechlab-net"
}

variable "app_client_id" {
  type    = string
}

variable "app_client_secret" {
  type    = string
}

variable "app_service_principal_id" {
  type    = string
}

variable "app_tenant_id" {
  type    = string
}

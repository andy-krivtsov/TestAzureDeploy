variable "name_prefix" {
  type     = string
#  default  = "demoapp"
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

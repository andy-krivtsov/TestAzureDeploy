variable "con_app_env" {
  type = string
}

variable "con_app_env_rg" {
  type = string
}

variable "con_app_env_cert" {
  type = string
}

variable "con_app_user_identity" {
  type = string
}

variable "app_global_env" {
  type = map(string)
}

variable "app_list" {
  type = map(object({
    args = list(string),
    envs = map(string)
  }))
}

variable "hostname_suffix" {
  type = string
}

variable "custom_domain" {
  type = string
}

variable "custom_dns_zone_rg" {
  type = string
}

variable "revision_suffix" {
  type = string
}

variable "app_image" {
  type = string
}

variable "app_tag" {
  default  = "dev"
  nullable = false
  type     = string
}

variable "acr_registry" {
  type = string
}

variable "acr_registry_rg" {
  type = string
}

variable "keyvault" {
  type = string
}

variable "keyvault_rg" {
  type = string
}

variable "keyvault_prefix" {
  type = string
}

variable "keyvault_secrets" {
  type = list(string)
  default = [
    "auth-client-id",
    "auth-client-secret",
    "auth-tenant-id",
    "auth-session-key"
  ]
}

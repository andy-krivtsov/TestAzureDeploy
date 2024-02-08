variable "app_name" {
  default = "demoapp"
  type    = string
}

variable "con_app_env_id" {
  type = string
}

variable "con_app_env_rg" {
  type = string
}

variable "con_app_user_identity_id" {
  type = string
}

variable "con_app_ip_address" {
  type = string
}

variable "secrets" {
  type = map(string)
}

variable "con_app_env_cert_id" {
  type = string
}

variable "app_hostname" {
  default = "demoapp"
  type    = string
}

variable "custom_domain" {
  type = string
}

variable "custom_dns_zone_rg" {
  type = string
}

variable "domain_verification_id" {
  type = string
}

variable "registry_server" {
  type = string
}

variable "revision_suffix" {
  type = string
}

variable "full_image_name" {
  type = string
}

variable "container_args" {
  type = list(string)
}

variable "cpu" {
  default = 0.25
  type    = number
}

variable "memory" {
  default = "0.5Gi"
  type    = string
}

variable "envs" {
  type = map(string)
}

variable "envs_secrets" {
  type = map(string)
}

variable "liveness_probe_path" {
  type    = string
  default = "/health/live"
}

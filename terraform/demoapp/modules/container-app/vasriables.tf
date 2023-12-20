variable "containerappName" {
  default  = "demoapp"
  type     = string
}

variable "containerappEnvId" {
  type     = string
}

variable "containerappEnvIpAddress" {
  type     = string
}

variable "customDomainVerificationId" {
  type     = string
}

variable "resourceGroupName" {
  type     = string
}

variable "userAssignedIdentityId" {
  type     = string
}

variable "customDnsZone" {
  type     = string
}

variable "customDnsZoneRG" {
  type     = string
}

variable "hostnameSuffix" {
  type     = string
}

variable "envCertificateId" {
  type     = string
}

variable "registryName" {
  type     = string
}

variable "revisionSuffix" {
  default  = ""
  type     = string
}

variable "fullImageName" {
  type     = string
}

variable "container_args" {
  type = list(string)
}

variable "cpu" {
  default = 0.25
  type     = number
}

variable "memory" {
  default = "0.5Gi"
  type     = string
}

variable "secrets" {
  type = map(string)
  default = {
    client-id = "demoid"
    client-secret = "demosecret"
  }
}

variable "envs" {
  type = map(string)
  default = {
    ENV_VAR_NAME = "VAR_VALUE"
  }
}

variable "envs_secrets" {
  type = map(string)
  default = {
    ENV_SECRET_VAR_NAME = "secret_name"
  }
}
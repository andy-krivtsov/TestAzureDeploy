variable "resourceGroupName" {
  default  = "AzureLearn"
  nullable = false
  type     = string
}

variable "storageAccountPrefix" {
  default  = "conappstor"
  nullable = false
  type     = string
}

variable "logWorkspacePrefix" {
  default  = "conapp-logs-"
  nullable = false
  type     = string
}

variable "environmentName" {
  default  = "demo-app-env"
  nullable = false
  type     = string
}

variable "containerappName" {
  default  = "demoapp"
  nullable = false
  type     = string
}

variable "registryName" {
  default  = "akazureregistry.azurecr.io"
  nullable = false
  type     = string
}

variable "containerImage" {
  default  = "learn/demoapp"
  nullable = false
  type     = string
}

variable "containerTag" {
  default  = "dev"
  nullable = false
  type     = string
}

variable "revisionSuffix" {
  default  = ""
  type     = string
}

variable "identityName" {
  default  = "DemoContainerApp"
  nullable = false
  type     = string
}

variable "authClientId" {
  type     = string
  nullable = false
}

variable "authClientSecret" {
  type     = string
  nullable = false
}

variable "authTenant" {
  type     = string
  nullable = false
}

variable "authSessionKey" {
  type     = string
  nullable = false
}


variable "customDomainHostname" {
  default  = "demoapp"
  nullable = false
  type     = string
}

variable "customDnsZone" {
  default  = "az.mechlab.net"
  nullable = false
  type     = string
}

variable "customDnsZoneRG" {
  default  = "AzureLearn"
  nullable = false
  type     = string
}


variable "certKeyVaultName" {
  default  = "ak-certs-vault"
  nullable = false
  type     = string
}

variable "certKeyVaultRG" {
  default  = "ssl-certs"
  nullable = false
  type     = string
}

variable "certKeyVaultKey" {
  default  = "wildcard-az-mechlab-net"
  nullable = false
  type     = string
}


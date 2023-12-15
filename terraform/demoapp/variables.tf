variable "namePrefix" {
  default  = "demoapp"
  nullable = false
  type     = string
}

variable "resourceGroupName" {
  default  = "AzureLearn"
  nullable = false
  type     = string
}

# variable "storageAccountPrefix" {
#   default  = "conappstor"
#   nullable = false
#   type     = string
# }

# variable "logWorkspacePrefix" {
#   default  = "conapp-logs-"
#   nullable = false
#   type     = string
# }

# variable "environmentName" {
#   default  = "demo-app-env"
#   nullable = false
#   type     = string
# }

# variable "containerappName" {
#   default  = "demoapp"
#   nullable = false
#   type     = string
# }

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

variable "secretsKeyVaultName" {
  default  = "ak-learn-vault"
  type     = string
}

variable "secretsKeyVaultRG" {
  default  = "AzureLearn"
  type     = string
}

variable "appKeyvaultSecrets" {
    type = map(string)
    default = {
      auth-client-id = "demoapp-client-id"
      auth-client-secret = "demoapp-client-secret"
      auth-tenant-id = "demoapp-tenant-id"
      auth-session-key = "demoapp-session-key"
    }
}
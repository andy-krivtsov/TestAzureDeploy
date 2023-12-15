
# User-facing Container App

resource "azurerm_container_app" "conapp" {
  name                         = var.containerappName
  container_app_environment_id = var.containerappEnvId
  resource_group_name          = var.resourceGroupName
  revision_mode                = "Single"

  depends_on = [
    time_sleep.wait_dns
  ]

  identity {
    type = "UserAssigned"
    identity_ids = [
      var.userAssignedIdentityId
    ]
  }

  dynamic "secret" {
    for_each = var.secrets
    content {
      name = secret.key
      value = secret.value
    }
  }

  ingress {
    external_enabled           = true
    target_port                = 8000
    allow_insecure_connections = false
    transport                  = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
    custom_domain {
      certificate_binding_type = "SniEnabled"
      certificate_id           = var.envCertificateId
      name                     = "${var.containerappName}.${var.customDnsZone}"
    }
  }

  registry {
    server   = var.registryName
    identity = var.userAssignedIdentityId
  }

  template {
    revision_suffix = var.revisionSuffix
    min_replicas    = 0
    max_replicas    = 1
    container {
      name   = var.containerappName
      image  = var.fullImageName
      args   = var.container_args

      cpu    = var.cpu
      memory = var.memory

      dynamic "env" {
          for_each = var.envs
          content {
              name = env.key
              value = env.value
          }
      }

      dynamic "env" {
          for_each = var.envs_secrets
          content {
              name = env.key
              secret_name = env.value
          }
      }

      liveness_probe {
        transport        = "HTTP"
        path             = "/health/live"
        port             = 8000
        initial_delay    = 10
        interval_seconds = 10
      }
    }
  }

}


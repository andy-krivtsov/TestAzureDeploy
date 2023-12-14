
# User-facing Container App

resource "azurerm_container_app" "conapp" {
  name                         = var.containerappName
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  resource_group_name          = data.azurerm_resource_group.rg.name
  revision_mode                = "Single"

  depends_on = [
    time_sleep.wait_dns,
    azurerm_servicebus_subscription.db_sub,
    azurerm_servicebus_subscription.stor_sub
  ]

  identity {
    type = "UserAssigned"
    identity_ids = [
      data.azurerm_user_assigned_identity.appIdentity.id
    ]
  }

  secret {
    name  = "client-id"
    value = var.authClientId
  }

  secret {
    name  = "client-secret"
    value = var.authClientSecret
  }

  secret {
    name  = "tenant"
    value = var.authClientSecret
  }

  secret {
    name  = "session-key"
    value = var.authSessionKey
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
      certificate_id           = azurerm_container_app_environment_certificate.appCert.id
      name                     = "${var.containerappName}.${var.customDnsZone}"
    }
  }

  registry {
    server   = var.registryName
    identity = data.azurerm_user_assigned_identity.appIdentity.id
  }

  template {
    revision_suffix = var.revisionSuffix
    min_replicas    = 0
    max_replicas    = 1
    container {
      name   = var.containerappName
      image  = local.fullImageName
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name = "AUTH_CLIENT_ID"
        secret_name = "client-id"
      }

      env {
        name = "AUTH_CLIENT_SECRET"
        secret_name = "client-secret"
      }

      env {
        name = "AUTH_TENANT"
        secret_name = "tenant"
      }

      env {
        name = "AUTH_SESSION_KEY"
        secret_name = "session-key"
      }

      liveness_probe {
        transport        = "HTTP"
        path             = "/"
        port             = 8000
        initial_delay    = 10
        interval_seconds = 3
      }
    }
  }

}


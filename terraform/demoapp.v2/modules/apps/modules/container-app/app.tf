
resource "azurerm_container_app" "conapp" {
  name                         = var.app_name
  container_app_environment_id = var.con_app_env_id
  resource_group_name          = var.con_app_env_rg
  revision_mode                = "Single"

  depends_on = [ time_sleep.wait_dns ]

  identity {
    type = "UserAssigned"
    identity_ids = [
      var.con_app_user_identity_id
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
      certificate_id           = var.con_app_env_cert_id
      name                     = "${var.app_hostname}.${var.custom_domain}"
    }
  }

  registry {
    server   = var.registry_server
    identity = var.con_app_user_identity_id
  }

  template {
    revision_suffix = var.revision_suffix
    min_replicas    = 0
    max_replicas    = 1
    container {
      name   = var.app_name
      image  = var.full_image_name
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
        path             = var.liveness_probe_path
        port             = 8000
        initial_delay    = 10
        interval_seconds = 10
      }
    }
  }

}


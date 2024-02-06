output "apps_url" {
  value = values(module.container_app)[*].app_url
}

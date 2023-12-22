output "app_url" {
  value = azurerm_container_app.conapp.ingress[0].custom_domain[0].name
}
output "client_id" {
  value = azuread_application.azuread_app.client_id
}

output "client_secret" {
  value     = azuread_application_password.azuread_app.value
  sensitive = true
}

output "tenant_id" {
  value = azuread_service_principal.azuread_app.application_tenant_id
}

output "service_principal_id" {
  value = azuread_service_principal.azuread_app.id
}


terraform {
  source = "../../../modules/aad_app_registration"
}

include "root" {
  path = find_in_parent_folders()
}

inputs = {
  display_name  = "Azure Demo App Dev"
  description   = "Azure demo application registration Local Dev(created by Terraform)"
  homepage_url  = "https://front-dev.az.mechlab.net"
  logout_url    = "https://front-dev.az.mechlab.net/logout"
  redirect_uris = [
    "https://front-dev.az.mechlab.net/token",
    "http://localhost:8000/token"
  ]
}


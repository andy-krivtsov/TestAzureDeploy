variable "display_name" {
  type = string
}

variable "description" {
  type = string
}

variable "homepage_url" {
  type = string
}

variable "logout_url" {
  type = string
}

variable "redirect_uris" {
  type = list(string)
}


# variable "azureadAppRegistration" {
#   type = object({
#     displayName = string,
#     description = string,
#     homepageUrl = string,
#     logoutUrl = string,
#     redirectUris = list(string)
#   })
#   default = {
#     displayName = "Azure Demo App"
#     description = "Azure demo application registration (created by Terraform)"
#     homepageUrl = "https://front.az.mechlab.net"
#     logoutUrl   = "https://front.az.mechlab.net/logout"
#     redirectUris = [
#       "https://front.az.mechlab.net/token",
#       "http://localhost:8000/token"
#     ]
#   }
# }

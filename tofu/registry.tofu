
resource "scaleway_registry_namespace" "main" {
  name        = "main-${var.glacier_vault_name}"
  description = "Main container registry"
  is_public   = false
}

resource "scaleway_iam_application" "registry" {
  name = "registry"
}

resource "scaleway_iam_api_key" "registry_key" {
  application_id = scaleway_iam_application.registry.id
}

resource scaleway_iam_policy "registry_access" {
  name = "registry_access"
  description = "gives app access to object registry"
  application_id = scaleway_iam_application.registry.id
  rule {
    project_ids = [ var.scaleway_project_id ]
    permission_set_names = [ "ContainerRegistryFullAccess" ]
  }
}

# ---------------------------------------------------------------------------- #
# outputs

output "registry" {
  value = scaleway_registry_namespace.main.id
}

output "registry-key" {
  value = scaleway_iam_api_key.registry_key.secret_key
  sensitive = true
}

output "registry-endpoint" {
  value = scaleway_registry_namespace.main.endpoint
}
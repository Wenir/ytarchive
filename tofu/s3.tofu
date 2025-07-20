# ---------------------------------------------------------------------------- #
# s3

resource "scaleway_object_bucket" "main" {
  name   = "${var.glacier_vault_name}-main"
  region = "nl-ams"

  lifecycle_rule {
    id      = "archive_id"
    enabled = true

    tags = {
      "archive" = "true"
    }

    transition {
      days          = 5
      storage_class = "GLACIER"
    }
  }

  lifecycle_rule {
    enabled                                = true
    abort_incomplete_multipart_upload_days = 30
  }
}

resource "scaleway_iam_policy" "s3_access" {
  name           = "s3_access"
  description    = "gives app access to object storage in project"
  application_id = scaleway_iam_application.job.id
  rule {
    project_ids          = [var.scaleway_project_id]
    permission_set_names = ["ObjectStorageFullAccess"]
  }
}

# ---------------------------------------------------------------------------- #
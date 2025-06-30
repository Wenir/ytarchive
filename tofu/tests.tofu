# ---------------------------------------------------------------------------- #
# s3

resource "scaleway_object_bucket" "tests" {
  name   = "${var.glacier_vault_name}-tests"
  region = "nl-ams"

  lifecycle_rule {
    enabled                                = true
    abort_incomplete_multipart_upload_days = 30
  }

  lifecycle_rule {
    enabled = true
    expiration {
        days = "2"
    }
  }
}

output "tests-bucket" {
  value = scaleway_object_bucket.tests.name
}

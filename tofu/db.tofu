# ---------------------------------------------------------------------------- #
# db

resource "scaleway_sdb_sql_database" "main" {
  name    = "main"
  min_cpu = 0
  max_cpu = 1
  region  = "fr-par"
}

resource "scaleway_iam_policy" "db_access" {
  name           = "db_access"
  description    = "gives app access to db in project"
  application_id = scaleway_iam_application.job.id
  rule {
    project_ids          = [var.scaleway_project_id]
    permission_set_names = ["ServerlessSQLDatabaseReadWrite"]
  }
}

# ---------------------------------------------------------------------------- #

locals {
  database_connection_string = format("postgres://%s:%s@%s",
    scaleway_iam_application.job.id,
    scaleway_iam_api_key.job_key.secret_key,
    trimprefix(scaleway_sdb_sql_database.main.endpoint, "postgres://"),
  )
}

# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
# alerts

data "scaleway_account_project" "ytarchive" {
  project_id = var.scaleway_project_id
}

data "scaleway_cockpit_preconfigured_alert" "all" {
  project_id = data.scaleway_account_project.ytarchive.id
}

resource "scaleway_cockpit_alert_manager" "main" {
  project_id = data.scaleway_account_project.ytarchive.id

  preconfigured_alert_ids = [
    for alert in data.scaleway_cockpit_preconfigured_alert.all.alerts :
    alert.preconfigured_rule_id
    if alert.name == "JobRunFailed" # && alert.rule_status == "disabled"
  ]

  contact_points {
    email = var.alert_email
  }
}
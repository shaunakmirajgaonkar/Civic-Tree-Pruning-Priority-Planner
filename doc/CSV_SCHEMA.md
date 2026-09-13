# CSV Schema

The tree inspection upload requires these exact columns:

`tree_id, tree_species, zone, street_name, latitude, longitude, tree_height_m, branch_condition_score, power_line_distance_m, pedestrian_use_index, wind_risk_index, inspection_condition_score, inspection_age_days, dead_branch_pct, canopy_density_pct, last_pruned_days, crew_access_score, near_school_score, near_road_score, recent_incident_count, work_order_status, last_inspection_date`

Scores are expected on a 0–100 scale unless the field is a distance, height, age, percentage, date, or count.

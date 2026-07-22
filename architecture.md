# Architecture

The supported system is the connected LightGBM path documented in the README: strict cohort validation, temporal-preferred split, training-only feature fitting, baseline comparison, immutable checksummed bundle, and one model-backed FastAPI service. Experimental transformer and earlier duplicate API surfaces are not release paths.

Production boundaries: the deployment supplies a trusted model directory and secret; readiness verifies the artifact; the API produces review recommendations rather than autonomous lending decisions; external IAM, ingress, storage, monitoring, and regulatory approvals remain environment responsibilities.

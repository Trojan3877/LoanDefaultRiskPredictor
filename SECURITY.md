# Security Policy

## Supported versions

Only the latest release and the default branch receive security fixes.

## Reporting a vulnerability

Do not open a public issue. Use GitHub's private vulnerability reporting for this repository. Include affected paths or versions, reproduction steps, impact, and a suggested mitigation when available.

## Response objectives

- Acknowledge a report within 3 business days.
- Triage severity and affected releases within 7 business days.
- Prioritize remediation using exploitability, data exposure, and service impact.
- Publish a security advisory and patched release when disclosure is safe.

## Security boundaries

This repository must not contain borrower data, credentials, cloud keys, model artifacts, or production configuration. Runtime secrets belong in the deployment platform's secret manager. Image consumers must verify the Cosign signature and deploy an immutable digest.

# Security Policy

## Supported version

Security fixes are applied to the `main` branch. Deployments should track a reviewed commit from
that branch. Frontend installations must use the committed `package-lock.json`. Python currently
uses reviewed, version-bounded manifests rather than a hash-locked, cross-platform resolution;
retain the resolved build artifact and audit it before promotion. A platform-aware Python lock with
hash verification remains a required follow-up before claiming fully reproducible backend builds.

## Reporting a vulnerability

Do not open a public issue for suspected vulnerabilities or disclose credentials, personal data,
documents, prompts, model output, or internal service URLs in an issue or pull request. Use the
repository owner's private GitHub security-reporting channel. Include the affected revision,
reproduction steps, impact, and a minimal proof of concept with all sensitive values redacted.

If private reporting is unavailable, contact the repository owner through an established private
organizational channel and request a secure disclosure path.

## Operational expectations

- Never commit `.env` files, tokens, passwords, certificates, production documents, or database
  files.
- Production must use `APP_ENV=production`, a unique secret key, non-wildcard allowed
  hosts, SSL redirect, secure cookies, HSTS, and a delivery-capable email backend. Browser
  origins and Jira URLs must use HTTPS when configured; Jira TLS verification cannot be disabled.
  Settings fail fast when these controls are weakened.
- AI services are loopback/private by default. Remote AI requires explicit
  `AI_ALLOW_REMOTE_SERVICES=true`, HTTPS in production, and approval for the classification of
  prompts, document text, and images that cross the host boundary.
- Keep OCR model downloads disabled during normal production operation.
- Treat document text, prompts, AI responses, Word cell contents, email bodies, and authentication
  headers as confidential and exclude them from logs.
- Reuse an `Idempotency-Key` only for the exact same notification request; use a new key for a
  deliberate new delivery. Reconcile a stale `pending` audit before choosing a new key because
  SMTP cannot provide an absolute exactly-once guarantee across a process crash.
- Run dependency audits in the network-enabled security workflow and investigate high or critical
  findings before release.

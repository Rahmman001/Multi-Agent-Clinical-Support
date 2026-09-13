# Security Policy

## Healthcare Privacy & Data Protection

**AegisClinical** is engineered from the ground up as a **privacy-first, air-gapped clinical intelligence engine**:

* **Zero Cloud PHI Egress**: All data processing, FHIR parsing, deterministic rule execution, and local SLM inference occur entirely on `127.0.0.1`.
* **No Telemetry / No Tracking**: AegisClinical does not include analytics, tracking pixels, or outbound telemetry pings.
* **HIPAA Security Rule (§ 164.312) Compatibility**: By keeping Protected Health Information (PHI) within the hospital local network perimeter, AegisClinical eliminates third-party cloud data-sharing risks.

---

## Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported |
| :--- | :--- |
| `1.0.x` | :white_check_mark: Yes |
| `< 1.0.0` | :x: No |

---

## Reporting a Vulnerability

If you discover a security vulnerability or potential data leak in AegisClinical, please report it responsibly:

1. **Do NOT open a public GitHub issue**.
2. Email your findings directly to the repository maintainer at:  
   **`contact@aegisclinical.local`** *(or reach out via GitHub Security Advisories)*.
3. Include:
   * A detailed description of the vulnerability.
   * Reproduction steps or proof of concept.
   * Potential clinical or data exposure implications.

We will acknowledge receipt within 48 hours and work with you to patch and release a fix before public disclosure.

---

## Medical Disclaimer

*AegisClinical is open-source research and educational software designed to demonstrate multi-agent clinical decision support architectures. It is not an FDA-cleared medical device and should not be used as the sole basis for clinical diagnosis, prescribing, or emergency patient care.*

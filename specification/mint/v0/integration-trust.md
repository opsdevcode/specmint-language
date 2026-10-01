# Integration trust model

Future trust levels, not implemented services:

| Level | Meaning |
| --- | --- |
| Official | Published by the Mint maintainers |
| Verified | Admitted after public review |
| Community | Author-published, unverified |

Future admission requirements: immutable version, artifact digest, signed
release, SBOM, provenance, conformance results, declared permissions,
security contact, compatibility range, supported targets and phases,
deprecation policy, and a vulnerability-response policy.

This repository does not provide a signing service, OCI delivery, hosted
registry, marketplace, or production trust service. v0 trusts only an
explicit local executable whose artifact digest matches the lock or
manifest, with no network and no ambient credentials.

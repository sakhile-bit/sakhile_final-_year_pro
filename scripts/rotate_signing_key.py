"""Generate a new certificate signing key and print rotation instructions.

Run:  python scripts/rotate_signing_key.py

Rotation never invalidates already-issued certificates: the old public key is
kept for verification (published via ZDH_PUBLIC_KEYS) while new certificates are
signed with the new key. Inspectors' verifiers fetch all public keys from
/verify/pubkey, so both old and new certificates keep verifying.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.security.certs import signing   # noqa: E402


def main() -> None:
    kp = signing.generate_keypair()

    # Try to capture the CURRENT active public key so we can advise keeping it
    # around for verification of already-issued certificates.
    current_kid = os.environ.get("ZDH_SIGNING_KEY_ID", "zdh-ed25519-1")
    current_pub = None
    try:
        current_pub = signing.get_signer().public_key_pem
    except Exception:
        pass

    new_kid = f"zdh-ed25519-{__import__('datetime').date.today():%Y%m%d}"

    print("=" * 70)
    print("NEW SIGNING KEY (set these on the portal, then restart it)")
    print("=" * 70)
    print(f"\nZDH_SIGNING_KEY_ID={new_kid}\n")
    print("ZDH_SIGNING_PRIVATE_KEY (keep secret!):\n")
    print(kp["private_pem"])

    print("=" * 70)
    print("KEEP OLD PUBLIC KEY FOR VERIFICATION")
    print("=" * 70)
    if current_pub:
        retired = {current_kid: current_pub}
        # Merge with any already-retired keys.
        try:
            existing = json.loads(os.environ.get("ZDH_PUBLIC_KEYS", "") or "{}")
            existing.update(retired)
            retired = existing
        except Exception:
            pass
        print("\nSet ZDH_PUBLIC_KEYS to (so old certificates still verify):\n")
        print("ZDH_PUBLIC_KEYS=" + json.dumps(retired))
    else:
        print("\n(Could not read the current public key — if this is the first "
              "key, there is nothing to retain.)")

    print("\n" + "=" * 70)
    print("New public key (for reference):")
    print("=" * 70)
    print(kp["public_pem"])


if __name__ == "__main__":
    main()

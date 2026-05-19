import os
from keycloak import KeycloakAdmin
import base64
# --- CONFIGURATION ---
KC_URL = "http://localhost:8080/"
DJANGO_URL = "http://172.18.255.200/"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
REALM_NAME = "myrealm"
CLIENT_ID = "django-client"
# ---------------------

def setup():
    try:
        # 1. Connect to Keycloak Master Realm
        admin = KeycloakAdmin(
            server_url=KC_URL,
            username=ADMIN_USER,
            password=ADMIN_PASS,
            realm_name="master",
            verify=False
        )

        # 2. Create Realm
        realms = [r['realm'] for r in admin.get_realms()]
        if REALM_NAME not in realms:
            admin.create_realm(payload={"realm": REALM_NAME, "enabled": True})
            print(f"[*] Realm '{REALM_NAME}' created.")
        
        admin.realm_name = REALM_NAME

        # 3. Create Client
        clients = admin.get_clients()
        client_internal_id = next((c['id'] for c in clients if c['clientId'] == CLIENT_ID), None)
        
        if not client_internal_id:
            client_payload = {
                "clientId": CLIENT_ID,
                "publicClient": False,
                "authorizationServicesEnabled": True,
                "serviceAccountsEnabled": True,
                "redirectUris": [f"{DJANGO_URL}*"],
                "webOrigins": ["*"],
                "rootUrl": DJANGO_URL,
                "enabled": True,
                "protocol": "openid-connect"
            }
            admin.create_client(payload=client_payload)
            client_internal_id = admin.get_client_id(CLIENT_ID)
            print(f"[*] Client '{CLIENT_ID}' created.")

        # 4. Create Role (django_root)
        roles = [r['name'] for r in admin.get_realm_roles()]
        if "django_root" not in roles:
            admin.create_realm_role(payload={"name": "django_root"})
            print("[*] Role 'django_root' created.")

        # 5. Create Test User
        user_id = admin.get_user_id("test_user")
        if not user_id:
            user_payload = {
                "username": "test_user",
                "enabled": True,
                "emailVerified": True,
                "credentials": [{"value": "123456", "type": "password", "temporary": False}]
            }
            admin.create_user(payload=user_payload)
            user_id = admin.get_user_id("test_user")
            print("[*] User 'test_user' created (Pass: 123456).")

        # 6. Assign Role to User
        role = admin.get_realm_role("django_root")
        admin.assign_realm_roles(user_id=user_id, roles=[role])
        print("[*] Role 'django_root' assigned to 'test_user'.")

        # 7. Get and Print Client Secret
        secret = admin.get_client_secrets(client_internal_id)['value']
        print("\n" + "="*50)
        print(f"YOUR CLIENT SECRET: {secret}")
        print("="*50)
        print("\nCopy this secret into your docker-compose.yml for OIDC_RP_CLIENT_SECRET")


        secret_bytes = secret.encode('utf-8')
        base64_secret = base64.b64encode(secret_bytes).decode('utf-8')

        secret_yaml = f"""apiVersion: v1
kind: Secret
metadata:
  name: django-secret
type: Opaque
data:
  CLIENT_SECRET: {base64_secret}
"""

        with open("django-secret.yaml", "w") as file:
            file.write(secret_yaml)

    except Exception as e:
        print(f"[!] Error: {str(e)}")

if __name__ == "__main__":
    setup()
# Keycloak

Open Source Identity and Access Management For Modern Applications and Services.

**[Website](https://www.keycloak.org/)** | **[Documentation](https://www.keycloak.org/documentation)** | **[GitHub](https://github.com/keycloak/keycloak)**

## How to enable?

```
platys init --enable-services KEYCLOAK
platys gen
```

## How to use it?

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28204>.
=======
Navigate to <http://10.156.72.251:28204>.
>>>>>>> Stashed changes

Login with user `admin` and password `abc123!`.

## How to export data from a realm

Replace `<realm-name>` by the name of the realm to export and <filename> by the file to write to (e.g. `data-transfer/xxxx-realm.json` to make it available outside of the container).

```bash
docker exec -it keycloak /opt/keycloak/bin/kc.sh --realm <realm-name> --file <filename>
```


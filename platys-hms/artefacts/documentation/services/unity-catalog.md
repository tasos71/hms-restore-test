# Unity Catalog

Open, Multi-modal Catalog for Data & AI.

**[Website](https://www.unitycatalog.io/)** | **[Documentation](https://docs.unitycatalog.io/)** | **[GitHub](https://github.com/unitycatalog/unitycatalog)**

## How to enable?

```bash
platys init --enable-services UNITY_CATALOG UNITY_CATALOG_UI
platys gen
```

## How to use it?

### Web UI

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28393>.
=======
Navigate to <http://10.156.72.251:28393>.
>>>>>>> Stashed changes

### Unity Catalog CLI

```bash
docker exec -ti unity-catalog bin/uc table list --catalog unity --schema default
```
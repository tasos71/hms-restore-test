# CKAN - The Open Source Data Portal Software

CKAN is an open-source DMS (data management system) for powering data hubs and data portals. CKAN makes it easy to publish, share and use data. It powers catalog.data.gov, open.canada.ca/data, data.humdata.org among many other sites. 

**[Website](https://ckan.org/)** | **[Documentation](https://docs.ckan.org/en/2.9/)** | **[GitHub](https://github.com/ckan/ckan)**

```bash
platys init --enable-services CKAN
platys gen
```

## How to use it?

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28294>.
=======
Navigate to <http://10.156.72.251:28294>.
>>>>>>> Stashed changes

### Using CLI

```bash
docker exec -ti ckan ckan -c /srv/app/production.ini 
```
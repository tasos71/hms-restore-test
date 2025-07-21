# Rancher

Rancher is a Kubernetes management tool to deploy and run clusters anywhere and on any provider.

**[Website](https://www.rancher.com/)** | **[Documentation](https://ranchermanager.docs.rancher.com)** | **[GitHub](https://github.com/rancher/rancher)**

## How to enable?

```
platys init --enable-services RANCHER
platys gen
```

## How to use it?

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28370>.
=======
Navigate to <http://10.156.72.251:28370>.
>>>>>>> Stashed changes

To get the initial password, execute the following

```bash
docker logs  rancher  2>&1 | grep "Bootstrap Password:"docker logs  rancher  2>&1 | grep "Bootstrap Password:"
```

# Chartboard

Simple dashboard to show widget chart 

**[Website](https://github.com/the-maux/Chartboard)** | **[Documentation](https://github.com/the-maux/tipboard/wiki)** | **[GitHub](https://github.com/the-maux/Chartboard)**

```
platys init --enable-services CHARTBOARD
platys gen
```

### Run Sample Dashboard

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28173> to see the sample dashboard.
=======
Navigate to <http://10.156.72.251:28173> to see the sample dashboard.
>>>>>>> Stashed changes

To simulate data, you can run the sensors inside the container

```
docker exec -ti chartboard python src/manage.py sensors
```


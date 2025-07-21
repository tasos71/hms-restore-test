# File Browser

A Web-based File Browser.

**[Documentation](https://filebrowser.org/)** | **[GitHub](https://github.com/filebrowser/filebrowser)** | **[Docker Image](https://github.com/hurlenko/filebrowser-docker)** 

## How to enable?

```
platys init --enable-services FILE_BROWSER
platys gen
```

## How to use it?

<<<<<<< Updated upstream
Navigate to <http://192.168.1.112:28178> and login with the default user `admin` and password `admin`. 
=======
Navigate to <http://10.156.72.251:28178> and login with the default user `admin` and password `admin`. 
>>>>>>> Stashed changes

### Changing password

Add to `config.yml`

```
FB_PASSWORD=<bcrypt-password>
```

To encrypt the password, you can run `docker run -ti hurlenko/filebrowser hash <password>`.
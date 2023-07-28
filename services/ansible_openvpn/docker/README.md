Create a file in this folder with your own generated credentials for the docker compose:

```shell
MYSQL_PASSWORD=DATABASE_PASSWORD
SEMAPHORE_ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD
SEMAPHORE_ACCESS_KEY_ENCRYPTION="YOUR_RANDOM_KEY"
MANAGEMENT_OPENVPN_PASSWORD=YOUR_OPENVPN_MANAGEMENT_CONSOLE_PASSWORD
MANAGEMENT_OPENVPN_PORT=5555
OPENVPN_STATUS_PATH=""
```

SEMAPHORE_ACCESS_KEY_ENCRYPTION value is generated with 

```shell
head -c32 /dev/urandom | base64
```

OPENVPN_STATUS_PATH could be `/var/log/openvpn/openvpn-status.log` if the container have access to it

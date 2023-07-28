# OpenVPN

* Initialize the configuration files and certificates

```bash
docker compose run --rm openvpn ovpn_genconfig -u udp://VPN.SERVERNAME.COM
docker compose run --rm openvpn ovpn_initpki
```

* Fix ownership (depending on how to handle your backups, this may not be needed)

```bash
sudo chown -R $(whoami): ./openvpn-data
```

* Start OpenVPN server process

```bash
docker compose up -d openvpn
```

* You can access the container logs with

```bash
docker compose logs -f
```

* Generate a client certificate

```bash
export CLIENTNAME="your_client_name"
# with a passphrase (recommended)
docker compose run --rm openvpn easyrsa build-client-full $CLIENTNAME
# without a passphrase (not recommended)
docker compose run --rm openvpn easyrsa build-client-full $CLIENTNAME nopass
```

* Retrieve the client configuration with embedded certificates

```bash
docker compose run --rm openvpn ovpn_getclient $CLIENTNAME > $CLIENTNAME.ovpn
```

* Revoke a client certificate

```bash
# Keep the corresponding crt, key and req files.
docker compose run --rm openvpn ovpn_revokeclient $CLIENTNAME
# Remove the corresponding crt, key and req files.
docker compose run --rm openvpn ovpn_revokeclient $CLIENTNAME remove
```

## Debugging Tips

* Create an environment variable with the name DEBUG and value of 1 to enable debug output (using "docker -e").

```bash
docker compose run -e DEBUG=1 -p 1194:1194/udp openvpn
```

# Ansible Semaphore


Create a file named .env in this folder with your own generated credentials for the docker compose:

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

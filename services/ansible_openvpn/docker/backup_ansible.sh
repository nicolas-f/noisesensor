# From
# https://docs.docker.com/storage/volumes/#back-up-restore-or-migrate-data-volumes
sudo docker run --rm --volumes-from semaphore-mysql-1 -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar /var/lib/mysql


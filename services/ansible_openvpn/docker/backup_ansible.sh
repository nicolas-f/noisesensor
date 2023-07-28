# From
# https://docs.docker.com/storage/volumes/#back-up-restore-or-migrate-data-volumes
# will save backup.tar in the current working directory
# mysql container should be shutdown before doing this backup
sudo docker run --rm --volumes-from semaphore-mysql-1 -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar /var/lib/mysql


FROM semaphoreui/semaphore:latest

USER root

RUN apk add rsync py3-pip

USER semaphore

CMD ["/usr/local/bin/semaphore-wrapper" "/usr/local/bin/semaphore" "server" "--config" "/etc/semaphore/config.json"]


#!/bin/bash

# Load container setup variables
for f in `cat conf/settings.env | grep =`; do export $f; done

# Define the image source
export IMAGE_SOURCE=${IMAGE_NAME}
[ ${DOCKER_REGISTRY} ] && export IMAGE_SOURCE=${DOCKER_REGISTRY}/${IMAGE_NAME}

docker run \
-d \
-v ./volumes:/some/path \
-p 80:80 \
--name ${CONTAINER_NAME} \
${IMAGE_SOURCE}:${IMAGE_TAG}

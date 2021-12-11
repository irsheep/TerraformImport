#!/bin/bash

# Load container setup variables
for f in `cat conf/settings.env | grep =`; do export $f; done

# Define the image source
export IMAGE_SOURCE=${IMAGE_NAME}
[ ${DOCKER_REGISTRY} ] && export IMAGE_SOURCE=${DOCKER_REGISTRY}/${IMAGE_NAME}

docker run \
-it \
--rm \
-v ./volumes:/some/path \
-p 8080:80 \
--name ${CONTAINER_NAME}-test \
${IMAGE_SOURCE}:${IMAGE_TAG}

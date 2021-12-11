#!/bin/bash 
  
# Load container setup variables
for f in `cat conf/settings.env | grep =`; do export $f; done

# Define the image source
export IMAGE_SOURCE=${IMAGE_NAME}
[ ${DOCKER_REGISTRY} ] && export IMAGE_SOURCE=${DOCKER_REGISTRY}/${IMAGE_NAME}

docker build \
-t ${IMAGE_SOURCE}:${IMAGE_TAG} \
-f conf/Dockerfile .

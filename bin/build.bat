@echo off

:: Load container setup variables
for /F "usebackq" %%i in (conf\settings.env) do set %%i

:: Define the image source
set IMAGE_SOURCE=%IMAGE_NAME%
if DEFINED DOCKER_REGISTRY (
    set IMAGE_SOURCE=%DOCKER_REGISTRY%/%IMAGE_NAME%
)

docker build ^
-t %IMAGE_SOURCE%:%IMAGE_TAG% ^
-f conf/Dockerfile .

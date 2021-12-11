@echo off

:: Load container setup variables
for /F "usebackq" %%i in (conf\settings.env) do set %%i

:: Define the image source
set IMAGE_SOURCE=%IMAGE_NAME%
if DEFINED DOCKER_REGISTRY (
    set IMAGE_SOURCE=%DOCKER_REGISTRY%/%IMAGE_NAME%
)

docker run ^
-it ^
--rm ^
-v %cd%\src:/opt/terraformimport ^
-v %cd%\volumes\data:/opt/terraformimport/data ^
--name %CONTAINER_NAME%-test ^
%IMAGE_SOURCE%:%IMAGE_TAG% /bin/bash
@echo off
REM =============================================================================
REM Docker Build Script for Baumaschinen-KI (Windows)
REM =============================================================================
REM This script builds both frontend and backend Docker images with proper
REM error handling and environment variable support
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
if "%DOCKER_REGISTRY%"=="" set DOCKER_REGISTRY=registry.digitalocean.com/ruekogpt1
set FRONTEND_IMAGE=%DOCKER_REGISTRY%/baumaschinen-frontend
set BACKEND_IMAGE=%DOCKER_REGISTRY%/baumaschinen-backend
if "%TAG%"=="" set TAG=latest

REM Build metadata
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set BUILD_DATE=%%c-%%a-%%b
if "%BUILD_VERSION%"=="" set BUILD_VERSION=%TAG%

REM Get git commit hash
for /f %%i in ('git rev-parse --short HEAD 2^>nul') do set VCS_REF=%%i
if "%VCS_REF%"=="" set VCS_REF=unknown

echo [INFO] Starting Docker build process...
echo [INFO] Registry: %DOCKER_REGISTRY%
echo [INFO] Tag: %TAG%
echo [INFO] Build Version: %BUILD_VERSION%
echo [INFO] VCS Ref: %VCS_REF%

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

REM Check for required environment variables for frontend
if "%VITE_API_URL%"=="" (
    echo [WARNING] VITE_API_URL not set. Frontend will use default or build-time value.
)

REM Build backend
echo [INFO] Building backend...
docker build ^
    --file backend\Dockerfile ^
    --tag %BACKEND_IMAGE%:%TAG% ^
    --tag %BACKEND_IMAGE%:latest ^
    backend

if errorlevel 1 (
    echo [ERROR] Backend build failed
    exit /b 1
)
echo [INFO] Backend built successfully!

REM Build frontend
echo [INFO] Building frontend...
docker build ^
    --file frontend\Dockerfile ^
    --tag %FRONTEND_IMAGE%:%TAG% ^
    --tag %FRONTEND_IMAGE%:latest ^
    --build-arg VITE_API_URL=%VITE_API_URL% ^
    --build-arg BUILD_VERSION=%BUILD_VERSION% ^
    --build-arg BUILD_DATE=%BUILD_DATE% ^
    --build-arg VCS_REF=%VCS_REF% ^
    frontend

if errorlevel 1 (
    echo [ERROR] Frontend build failed
    exit /b 1
)
echo [INFO] Frontend built successfully!

echo [INFO] All images built successfully!

REM List built images
echo [INFO] Built images:
docker images | findstr /i "baumaschinen"

REM Optional: Push to registry
if "%PUSH_TO_REGISTRY%"=="true" (
    echo [INFO] Pushing images to registry...

    docker push %BACKEND_IMAGE%:%TAG%
    docker push %BACKEND_IMAGE%:latest
    docker push %FRONTEND_IMAGE%:%TAG%
    docker push %FRONTEND_IMAGE%:latest

    echo [INFO] Images pushed to registry successfully!
) else (
    echo [INFO] To push images to registry, set PUSH_TO_REGISTRY=true
)

endlocal
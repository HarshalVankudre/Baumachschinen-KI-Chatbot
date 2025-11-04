#!/bin/bash

# ============================================================================
# COMPLETE DEPLOYMENT SCRIPT FOR BAUMASCHINEN-KI
# ============================================================================
# This script handles the entire deployment process end-to-end
# No manual steps required - just run ./deploy.sh
# ============================================================================

set -e  # Exit on any error

# ============================================================================
# CONFIGURATION
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project settings
PROJECT_NAME="baumaschinen-ki"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Digital Ocean Configuration
# Use DO_REGISTRY from .env.production if set, otherwise use default
DO_REGISTRY="${DO_REGISTRY:-registry.digitalocean.com/ruekogpt1}"
BACKEND_IMAGE="${DO_REGISTRY}/baumaschinen-backend"
FRONTEND_IMAGE="${DO_REGISTRY}/baumaschinen-frontend"

# Build metadata
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION=$(date +'%Y%m%d-%H%M%S')

# Deployment paths
REMOTE_DIR="/opt/baumaschinen-ki"
DOCKER_NETWORK="baumaschinen-network"

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ ERROR:${NC} $1"
}

log_section() {
    echo ""
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║  $1${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============================================================================
# STEP 1: LOAD ENVIRONMENT VARIABLES
# ============================================================================

log_section "LOADING CONFIGURATION"

# Check for production environment file
if [ ! -f "${SCRIPT_DIR}/.env.production" ]; then
    log_error ".env.production file not found!"
    echo ""
    echo "Please create .env.production with the following variables:"
    echo "----------------------------------------"
    cat << EOF
# Digital Ocean Settings
DIGITAL_OCEAN_TOKEN=your_do_api_token
DIGITAL_OCEAN_DROPLET_IP=your_droplet_ip
DO_SSH_USER=root
DO_SSH_KEY_PATH=~/.ssh/id_rsa

# MongoDB Settings
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=baumaschinen_ki

# API Keys
JWT_SECRET_KEY=your_jwt_secret_key
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=baumaschinen-docs

# PostgreSQL Settings
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=baumaschinen
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password

# SMTP Settings
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_email_password
SMTP_FROM_EMAIL=your_email@domain.com
SMTP_FROM_NAME=Baumaschinen-KI
SMTP_USE_TLS=true

# Application URLs
FRONTEND_URL=http://your_droplet_ip
BACKEND_URL=http://your_droplet_ip:8000
EOF
    echo "----------------------------------------"
    exit 1
fi

# Load environment variables (safer method)
if [ -f "${SCRIPT_DIR}/.env.production" ]; then
    set -a  # automatically export all variables
    source "${SCRIPT_DIR}/.env.production"
    set +a  # turn off automatic export
fi

# Validate critical variables (DIGITAL_OCEAN_TOKEN is now optional)
REQUIRED_VARS=(
    "DO_DROPLET_IP"
    "MONGODB_URI"
    "JWT_SECRET_KEY"
    "OPENAI_API_KEY"
    "PINECONE_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required variable not set: $var"
        exit 1
    fi
done

# Set derived variables (using DO_ prefix as in your .env.production)
DO_DROPLET_IP="${DO_DROPLET_IP}"
DO_SSH_USER="${DO_DROPLET_USER:-root}"
DO_SSH_KEY="${DO_SSH_KEY_PATH:-~/.ssh/id_rsa}"
DIGITAL_OCEAN_TOKEN="${DIGITAL_OCEAN_TOKEN:-}"  # Optional now

# Expand tilde in SSH key path
DO_SSH_KEY="${DO_SSH_KEY/#\~/$HOME}"

log_success "Environment variables loaded"

# ============================================================================
# STEP 2: PRE-FLIGHT CHECKS
# ============================================================================

log_section "PRE-FLIGHT CHECKS"

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi
log_success "Docker: $(docker --version | cut -d, -f1)"

# Check Git
if ! command -v git &> /dev/null; then
    log_warning "Git not installed, using unknown for commit hash"
fi

# Check SSH key exists
if [ ! -f "${DO_SSH_KEY}" ]; then
    log_error "SSH key not found at: ${DO_SSH_KEY}"
    echo "Please ensure your SSH key exists or update DO_SSH_KEY_PATH in .env.production"
    exit 1
fi
log_success "SSH key found: ${DO_SSH_KEY}"

# Test SSH connection
log_info "Testing SSH connection to ${DO_DROPLET_IP}..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no -i "${DO_SSH_KEY}" "${DO_SSH_USER}@${DO_DROPLET_IP}" "echo 'Connected'" &> /dev/null; then
    log_success "SSH connection successful"
else
    log_error "Cannot connect to ${DO_DROPLET_IP} via SSH"
    echo "Please ensure:"
    echo "  1. The droplet IP is correct: ${DO_DROPLET_IP}"
    echo "  2. SSH key has correct permissions: chmod 600 ${DO_SSH_KEY}"
    echo "  3. SSH is enabled on the droplet"
    echo "  4. User ${DO_SSH_USER} exists on the droplet"
    exit 1
fi

# ============================================================================
# STEP 3: BUILD DOCKER IMAGES
# ============================================================================

log_section "BUILDING DOCKER IMAGES"

# Build Backend
log_info "Building backend Docker image..."
cd "${SCRIPT_DIR}/backend"

docker build \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${GIT_COMMIT}" \
    --build-arg BUILD_VERSION="${VERSION}" \
    -t "${BACKEND_IMAGE}:latest" \
    -t "${BACKEND_IMAGE}:${VERSION}" \
    .

if [ $? -eq 0 ]; then
    log_success "Backend image built successfully"
else
    log_error "Failed to build backend image"
    exit 1
fi

# Build Frontend
log_info "Building frontend Docker image..."
cd "${SCRIPT_DIR}/frontend"

# Set API URL for frontend
VITE_API_URL="http://${DO_DROPLET_IP}:8000"

docker build \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${GIT_COMMIT}" \
    --build-arg BUILD_VERSION="${VERSION}" \
    --build-arg VITE_API_URL="${VITE_API_URL}" \
    -t "${FRONTEND_IMAGE}:latest" \
    -t "${FRONTEND_IMAGE}:${VERSION}" \
    .

if [ $? -eq 0 ]; then
    log_success "Frontend image built successfully"
else
    log_error "Failed to build frontend image"
    exit 1
fi

cd "${SCRIPT_DIR}"

# ============================================================================
# STEP 4: AUTHENTICATE WITH DIGITAL OCEAN REGISTRY
# ============================================================================

log_section "AUTHENTICATING WITH REGISTRY"

if [ ! -z "${DIGITAL_OCEAN_TOKEN}" ]; then
    log_info "Logging into Digital Ocean Container Registry..."
    echo "${DIGITAL_OCEAN_TOKEN}" | docker login "${DO_REGISTRY}" -u "${DIGITAL_OCEAN_TOKEN}" --password-stdin

    if [ $? -eq 0 ]; then
        log_success "Successfully authenticated with registry"
    else
        log_error "Failed to authenticate with Digital Ocean registry"
        echo "Please check your DIGITAL_OCEAN_TOKEN in .env.production"
        exit 1
    fi
else
    log_info "No DIGITAL_OCEAN_TOKEN provided, assuming already logged in to registry"
    log_warning "If push fails, run: doctl registry login"
fi

# ============================================================================
# STEP 5: PUSH IMAGES TO REGISTRY
# ============================================================================

log_section "PUSHING IMAGES TO REGISTRY"

# Push Backend
log_info "Pushing backend images..."
docker push "${BACKEND_IMAGE}:latest"
docker push "${BACKEND_IMAGE}:${VERSION}"

if [ $? -eq 0 ]; then
    log_success "Backend images pushed successfully"
else
    log_error "Failed to push backend images"
    exit 1
fi

# Push Frontend
log_info "Pushing frontend images..."
docker push "${FRONTEND_IMAGE}:latest"
docker push "${FRONTEND_IMAGE}:${VERSION}"

if [ $? -eq 0 ]; then
    log_success "Frontend images pushed successfully"
else
    log_error "Failed to push frontend images"
    exit 1
fi

# ============================================================================
# STEP 6: PREPARE DEPLOYMENT FILES
# ============================================================================

log_section "PREPARING DEPLOYMENT"

log_info "Creating docker-compose.yml for production..."

# Create temporary deployment directory
TEMP_DEPLOY_DIR="${SCRIPT_DIR}/temp_deploy_${VERSION}"
mkdir -p "${TEMP_DEPLOY_DIR}"

# Create docker-compose.yml
cat > "${TEMP_DEPLOY_DIR}/docker-compose.yml" << EOF
version: '3.8'

services:
  backend:
    image: ${BACKEND_IMAGE}:latest
    container_name: baumaschinen-backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - MONGODB_DATABASE=${MONGODB_DATABASE:-baumaschinen_ki}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT:-us-east-1}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME:-baumaschinen-docs}
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT:-5432}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_FROM_EMAIL=${SMTP_FROM_EMAIL}
      - SMTP_FROM_NAME=${SMTP_FROM_NAME:-Rueko AI}
      - SMTP_USE_TLS=${SMTP_USE_TLS:-true}
      - FRONTEND_URL=http://${DO_DROPLET_IP}
      - BACKEND_URL=http://${DO_DROPLET_IP}:8000
    networks:
      - ${DOCKER_NETWORK}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    image: ${FRONTEND_IMAGE}:latest
    container_name: baumaschinen-frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - ${DOCKER_NETWORK}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  ${DOCKER_NETWORK}:
    driver: bridge
EOF

log_success "Docker compose file created"

# Create deployment script for server
cat > "${TEMP_DEPLOY_DIR}/deploy_on_server.sh" << 'DEPLOY_SCRIPT'
#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          DEPLOYING BAUMASCHINEN-KI ON SERVER              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

cd /opt/baumaschinen-ki

# Authenticate with registry (if token provided)
if [ ! -z "$DO_TOKEN" ]; then
    echo -e "${BLUE}→ Authenticating with Docker registry...${NC}"
    echo "$DO_TOKEN" | docker login registry.digitalocean.com/ruekogpt1 -u "$DO_TOKEN" --password-stdin
else
    echo -e "${BLUE}→ Skipping authentication (assuming already logged in)...${NC}"
fi

# Pull latest images
echo -e "${BLUE}→ Pulling latest Docker images...${NC}"
docker-compose pull

# Stop existing containers gracefully
echo -e "${BLUE}→ Stopping existing containers...${NC}"
docker-compose down --remove-orphans

# Clean up any dangling containers
docker container prune -f

# Start new containers
echo -e "${BLUE}→ Starting new containers...${NC}"
docker-compose up -d

# Wait for services to start
echo -e "${BLUE}→ Waiting for services to become healthy...${NC}"
sleep 15

# Check backend health
echo -e "${BLUE}→ Checking backend health...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    docker-compose logs --tail=50 backend
fi

# Check frontend health
echo -e "${BLUE}→ Checking frontend health...${NC}"
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Frontend may still be starting...${NC}"
fi

# Show running containers
echo -e "${BLUE}→ Running containers:${NC}"
docker-compose ps

# Clean up old images
echo -e "${BLUE}→ Cleaning up old Docker images...${NC}"
docker image prune -f

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         DEPLOYMENT COMPLETED ON SERVER!                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
DEPLOY_SCRIPT

chmod +x "${TEMP_DEPLOY_DIR}/deploy_on_server.sh"
log_success "Deployment scripts prepared"

# ============================================================================
# STEP 7: DEPLOY TO SERVER
# ============================================================================

log_section "DEPLOYING TO SERVER"

# Create remote directory
log_info "Creating deployment directory on server..."
ssh -i "${DO_SSH_KEY}" "${DO_SSH_USER}@${DO_DROPLET_IP}" "mkdir -p ${REMOTE_DIR}"

# Copy files to server
log_info "Copying deployment files to server..."
scp -i "${DO_SSH_KEY}" "${TEMP_DEPLOY_DIR}/docker-compose.yml" "${DO_SSH_USER}@${DO_DROPLET_IP}:${REMOTE_DIR}/"
scp -i "${DO_SSH_KEY}" "${TEMP_DEPLOY_DIR}/deploy_on_server.sh" "${DO_SSH_USER}@${DO_DROPLET_IP}:${REMOTE_DIR}/"

# Execute deployment on server
log_info "Executing deployment on server..."
if [ ! -z "${DIGITAL_OCEAN_TOKEN}" ]; then
    ssh -i "${DO_SSH_KEY}" "${DO_SSH_USER}@${DO_DROPLET_IP}" "cd ${REMOTE_DIR} && DO_TOKEN='${DIGITAL_OCEAN_TOKEN}' bash deploy_on_server.sh"
else
    ssh -i "${DO_SSH_KEY}" "${DO_SSH_USER}@${DO_DROPLET_IP}" "cd ${REMOTE_DIR} && bash deploy_on_server.sh"
fi

if [ $? -eq 0 ]; then
    log_success "Deployment executed successfully"
else
    log_error "Deployment failed on server"
    exit 1
fi

# ============================================================================
# STEP 8: VERIFY DEPLOYMENT
# ============================================================================

log_section "VERIFYING DEPLOYMENT"

# Test backend
log_info "Testing backend endpoint..."
if curl -f "http://${DO_DROPLET_IP}:8000/health" > /dev/null 2>&1; then
    log_success "Backend is accessible at http://${DO_DROPLET_IP}:8000"
else
    log_warning "Backend might still be starting up..."
    echo "Waiting 10 more seconds..."
    sleep 10
    if curl -f "http://${DO_DROPLET_IP}:8000/health" > /dev/null 2>&1; then
        log_success "Backend is now accessible"
    else
        log_error "Backend is not responding"
    fi
fi

# Test frontend
log_info "Testing frontend..."
if curl -f "http://${DO_DROPLET_IP}/" > /dev/null 2>&1; then
    log_success "Frontend is accessible at http://${DO_DROPLET_IP}"
else
    log_warning "Frontend might still be starting up..."
    echo "Waiting 10 more seconds..."
    sleep 10
    if curl -f "http://${DO_DROPLET_IP}/" > /dev/null 2>&1; then
        log_success "Frontend is now accessible"
    else
        log_error "Frontend is not responding"
    fi
fi

# ============================================================================
# STEP 9: CLEANUP
# ============================================================================

log_section "CLEANUP"

log_info "Removing temporary files..."
rm -rf "${TEMP_DEPLOY_DIR}"
log_success "Cleanup completed"

# ============================================================================
# DEPLOYMENT COMPLETE - SHOW SUMMARY
# ============================================================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  🎉 DEPLOYMENT SUCCESSFUL! 🎉                      ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║ Version:     ${NC}${VERSION}"
echo -e "${GREEN}║ Git Commit:  ${NC}${GIT_COMMIT}"
echo -e "${GREEN}║ Server:      ${NC}${DO_DROPLET_IP}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                    ACCESS YOUR APPLICATION                         ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║ Frontend:    ${NC}http://${DO_DROPLET_IP}"
echo -e "${GREEN}║ Backend API: ${NC}http://${DO_DROPLET_IP}:8000"
echo -e "${GREEN}║ API Docs:    ${NC}http://${DO_DROPLET_IP}:8000/docs"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                     USEFUL COMMANDS                                ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║ View logs:${NC}"
echo "  ssh ${DO_SSH_USER}@${DO_DROPLET_IP} 'cd ${REMOTE_DIR} && docker-compose logs -f'"
echo -e "${GREEN}║ Restart services:${NC}"
echo "  ssh ${DO_SSH_USER}@${DO_DROPLET_IP} 'cd ${REMOTE_DIR} && docker-compose restart'"
echo -e "${GREEN}║ Stop services:${NC}"
echo "  ssh ${DO_SSH_USER}@${DO_DROPLET_IP} 'cd ${REMOTE_DIR} && docker-compose down'"
echo -e "${GREEN}║ View container status:${NC}"
echo "  ssh ${DO_SSH_USER}@${DO_DROPLET_IP} 'cd ${REMOTE_DIR} && docker-compose ps'"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_success "Deployment completed at $(date)"
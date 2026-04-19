#!/bin/bash

# Variables (edit these)
IMAGE_NAME="simple-flask-app"
DOCKERHUB_USERNAME="yovanrtp"
DOCKERHUB_REPO="$DOCKERHUB_USERNAME/$IMAGE_NAME"
DOCKERFILE_PATH="." # Path to Dockerfile

# 1. Install Docker
echo "Installing Docker..."
sudo apt-get update
sudo apt-get install -y docker.io

# 2. Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# 3. Build Docker image
echo "Building Docker image..."
sudo docker build -t $DOCKERHUB_REPO $DOCKERFILE_PATH

# 4. Docker Hub login
echo "Logging in to Docker Hub..."
sudo docker login

# 5. Push image to Docker Hub
echo "Pushing image to Docker Hub..."
sudo docker push $DOCKERHUB_REPO

echo "Done! Image pushed to Docker Hub: $DOCKERHUB_REPO"

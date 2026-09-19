```groovy
pipeline {

    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    environment {

        // AWS
        AWS_REGION = 'us-east-1'

        // ECR
        ECR_REPOSITORY = 'jenkins-demo'

        // EKS
        EKS_CLUSTER = 'demo-eks'

        // Kubernetes
        K8S_NAMESPACE = 'jenkins-demo'
    }

    stages {

        /*
         * ============================================
         * CHECKOUT
         * ============================================
         */

        stage('Checkout') {
            steps {

                echo 'Checking out source code...'

                checkout scm

                script {

                    // Get Git commit
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    // Get AWS account ID
                    env.AWS_ACCOUNT_ID = sh(
                        script: '''
                            aws sts get-caller-identity \
                            --query Account \
                            --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    // Create unique image tag
                    env.IMAGE_TAG =
                        "${BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"

                    // ECR registry
                    env.ECR_REGISTRY =
                        "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"

                    // Full Docker image
                    env.IMAGE_URI =
                        "${env.ECR_REGISTRY}/${env.ECR_REPOSITORY}:${env.IMAGE_TAG}"
                }

                echo "=========================================="
                echo "Git Commit    : ${env.GIT_COMMIT_SHORT}"
                echo "AWS Account   : ${env.AWS_ACCOUNT_ID}"
                echo "AWS Region    : ${env.AWS_REGION}"
                echo "ECR Repository: ${env.ECR_REPOSITORY}"
                echo "Image         : ${env.IMAGE_URI}"
                echo "EKS Cluster   : ${env.EKS_CLUSTER}"
                echo "=========================================="
            }
        }


        /*
         * ============================================
         * TEST
         * ============================================
         */

        stage('Test') {
            steps {

                echo 'Running application tests...'

                sh '''
                    set -eux

                    python3 --version
                    pip3 --version

                    python3 -m venv .venv

                    . .venv/bin/activate

                    pip install --upgrade pip

                    pip install -r requirements.txt

                    pip install pytest

                    pytest -v
                '''
            }
        }


        /*
         * ============================================
         * DOCKER BUILD
         * ============================================
         */

        stage('Docker Build') {
            steps {

                echo 'Building Docker image...'

                sh '''
                    set -eux

                    docker build \
                        -t "${IMAGE_URI}" \
                        -t "${ECR_REGISTRY}/${ECR_REPOSITORY}:latest" \
                        .
                '''
            }
        }


        /*
         * ============================================
         * ECR LOGIN
         * ============================================
         */

        stage('ECR Login') {
            steps {

                echo 'Logging in to Amazon ECR...'

                sh '''
                    set -eux

                    aws ecr get-login-password \
                        --region "${AWS_REGION}" \
                    | docker login \
                        --username AWS \
                        --password-stdin "${ECR_REGISTRY}"
                '''
            }
        }


        /*
         * ============================================
         * PUSH IMAGE TO ECR
         * ============================================
         */

        stage('Push to ECR') {
            steps {

                echo 'Pushing Docker image to ECR...'

                sh '''
                    set -eux

                    echo "Pushing versioned image:"
                    echo "${IMAGE_URI}"

                    docker push "${IMAGE_URI}"

                    echo "Pushing latest image:"

                    docker push \
                        "${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"
                '''
            }
        }


        /*
         * ============================================
         * EKS AUTHENTICATION
         * ============================================
         */

        stage('EKS Authentication') {
            steps {

                echo 'Connecting to EKS...'

                sh '''
                    set -eux

                    echo "Updating kubeconfig..."

                    aws eks update-kubeconfig \
                        --region "${AWS_REGION}" \
                        --name "${EKS_CLUSTER}"

                    echo "Checking Kubernetes connection..."

                    kubectl cluster-info

                    echo "Checking EKS nodes..."

                    kubectl get nodes
                '''
            }
        }


        /*
         * ============================================
         * DEPLOY TO EKS
         * ============================================
         */

        stage('Deploy to EKS') {
            steps {

                echo 'Deploying application to EKS...'

                sh '''
                    set -eux

                    echo "Creating namespace..."

                    kubectl apply \
                        -f k8s/namespace.yaml


                    echo "Deploying application..."

                    sed \
                        "s|IMAGE_PLACEHOLDER|${IMAGE_URI}|g" \
                        k8s/deployment.yaml \
                        | kubectl apply -f -


                    echo "Creating/updating service..."

                    kubectl apply \
                        -f k8s/service.yaml
                '''
            }
        }


        /*
         * ============================================
         * ROLLOUT
         * ============================================
         */

        stage('Rollout Verification') {
            steps {

                echo 'Waiting for Kubernetes rollout...'

                sh '''
                    set -eux

                    kubectl rollout status \
                        deployment/jenkins-demo \
                        -n "${K8S_NAMESPACE}" \
                        --timeout=180s
                '''
            }
        }


        /*
         * ============================================
         * VERIFY DEPLOYMENT
         * ============================================
         */

        stage('Deployment Verification') {
            steps {

                echo 'Verifying Kubernetes deployment...'

                sh '''
                    set -eux

                    echo "=========================================="
                    echo "DEPLOYMENT"
                    echo "=========================================="

                    kubectl get deployment \
                        jenkins-demo \
                        -n "${K8S_NAMESPACE}" \
                        -o wide


                    echo "=========================================="
                    echo "PODS"
                    echo "=========================================="

                    kubectl get pods \
                        -n "${K8S_NAMESPACE}" \
                        -o wide


                    echo "=========================================="
                    echo "SERVICE"
                    echo "=========================================="

                    kubectl get service \
                        jenkins-demo \
                        -n "${K8S_NAMESPACE}"


                    echo "=========================================="
                    echo "IMAGE"
                    echo "=========================================="

                    kubectl get deployment \
                        jenkins-demo \
                        -n "${K8S_NAMESPACE}" \
                        -o jsonpath='{.spec.template.spec.containers[0].image}'

                    echo
                '''
            }
        }
    }


    /*
     * ================================================
     * POST ACTIONS
     * ================================================
     */

    post {

        success {

            echo '''
========================================
       DEPLOYMENT SUCCESSFUL
========================================
'''

            echo "Application : jenkins-demo"
            echo "Image       : ${env.IMAGE_URI}"
            echo "EKS Cluster : ${env.EKS_CLUSTER}"
            echo "Namespace   : ${env.K8S_NAMESPACE}"
            echo "Region      : ${env.AWS_REGION}"
        }


        failure {

            echo '''
========================================
       BUILD / DEPLOYMENT FAILED
========================================
'''

            echo "Check the failed stage above."
        }


        always {

            echo 'Cleaning Docker images...'

            sh '''
                docker image prune -f || true
            '''

            deleteDir()
        }
    }
}
```

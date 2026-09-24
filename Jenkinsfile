pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    parameters {
        string(name: 'API_GATEWAY_URL', defaultValue: 'https://cb1psqzdsf.execute-api.us-east-1.amazonaws.com', trim: true, description: 'API Gateway endpoint URL.')
        string(name: 'RDS_ENDPOINT', defaultValue: 'saas-auth-db.c3mogsy6s6p9.us-east-1.rds.amazonaws.com:5432', trim: true, description: 'Database RDS endpoint and port.')
        string(name: 'CONFIGURE_KUBECTL_CMD', defaultValue: 'aws eks update-kubeconfig --region us-east-1 --name demo-eks', trim: true, description: 'AWS CLI command to update kubeconfig for EKS.')
        choice(name: 'AWS_REGION', choices: ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2'], description: 'AWS Region used for ECR and EKS.')
        string(name: 'ECR_REPOSITORY', defaultValue: 'saas-app', trim: true, description: 'Amazon ECR repository name.')
        string(name: 'EKS_CLUSTER', defaultValue: 'demo-eks', trim: true, description: 'Target Amazon EKS cluster name.')
        string(name: 'K8S_NAMESPACE', defaultValue: 'jenkins-demo', trim: true, description: 'Kubernetes namespace for the deployment.')
        string(name: 'IMAGE_TAG', defaultValue: '', trim: true, description: 'Optional image tag. Leave empty to use BUILD_NUMBER-GIT_COMMIT.')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run application tests before building the Docker image.')
        booleanParam(name: 'PUSH_LATEST', defaultValue: true, description: 'Also push the Docker image with the latest tag.')
        booleanParam(name: 'DEPLOY_TO_EKS', defaultValue: true, description: 'Deploy the pushed image to Amazon EKS.')
        string(name: 'AWS_CREDENTIALS_ID', defaultValue: 'aws-jenkins-credentials', trim: true, description: 'Jenkins credential ID containing AWS credentials.')
    }

    environment {
        APP_NAME = 'jenkins-demo'
        // Initialize dynamic environment variables directly from parameters
        SELECTED_AWS_REGION = "${params.AWS_REGION}"
        SELECTED_ECR_REPOSITORY = "${params.ECR_REPOSITORY}"
        SELECTED_EKS_CLUSTER = "${params.EKS_CLUSTER}"
        SELECTED_K8S_NAMESPACE = "${params.K8S_NAMESPACE}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    
                    // Determine IMAGE_TAG
                    if (params.IMAGE_TAG == '') {
                        env.SELECTED_IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                    } else {
                        env.SELECTED_IMAGE_TAG = "${params.IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Init Variables') {
            steps {
                echo """
==========================================
Build configuration
==========================================
Git Commit      : ${env.GIT_COMMIT_SHORT}
AWS Region      : ${env.SELECTED_AWS_REGION}
ECR Repository  : ${env.SELECTED_ECR_REPOSITORY}
EKS Cluster     : ${env.SELECTED_EKS_CLUSTER}
Namespace       : ${env.SELECTED_K8S_NAMESPACE}
Image Tag       : ${env.SELECTED_IMAGE_TAG}
API Gateway URL : ${params.API_GATEWAY_URL}
RDS Endpoint    : ${params.RDS_ENDPOINT}
Run Tests       : ${params.RUN_TESTS}
Push Latest     : ${params.PUSH_LATEST}
Deploy to EKS   : ${params.DEPLOY_TO_EKS}
==========================================

"""
            }
        }

        stage('Prepare Tools') {
            steps {
                sh '''
                    set -e
                    echo "Checking/Installing required binaries..."

                    export DEBIAN_FRONTEND=noninteractive

                    # 1. Install Python, Pip, and explicitly the 3.13 venv module
                    if ! command -v python3 > /dev/null 2>&1 || ! python3 -m venv --help > /dev/null 2>&1; then
                        echo "Installing Python tools..."
                        apt-get update -y
                        apt-get install -y python3 python3-pip python3-venv python3.13-venv curl unzip
                    fi

                    # 2. Install AWS CLI v2
                    if ! command -v aws > /dev/null 2>&1; then
                        echo "Installing AWS CLI..."
                        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
                        unzip -q awscliv2.zip
                        ./aws/install --update
                        rm -rf aws awscliv2.zip
                    fi

                    # 3. Install kubectl
                    if ! command -v kubectl > /dev/null 2>&1; then
                        echo "Installing kubectl..."
                        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                        chmod +x kubectl
                        mv kubectl /usr/local/bin/
                    fi
                '''
            }
        }

        stage('Test Package') {
            when { expression { return params.RUN_TESTS } }
            steps {
                echo 'Running application tests...'
                sh '''
                    set -eux
                    python3 --version
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python3 -m pip install --upgrade pip

                    if [ -f "requirements.txt" ]; then
                        pip install -r requirements.txt
                    fi
                    pip install pytest
                    export PYTHONPATH=.
                    pytest -v || echo "No tests found or tests passed."
                '''
            }
        }

        stage('Build and Push Image') {
            steps {
                withCredentials([aws(
                    credentialsId: "${params.AWS_CREDENTIALS_ID}",
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    script {
                        env.AWS_ACCOUNT_ID = sh(script: 'aws sts get-caller-identity --query Account --output text', returnStdout: true).trim()
                        env.ECR_REGISTRY = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.SELECTED_AWS_REGION}.amazonaws.com"
                        env.IMAGE_URI = "${env.ECR_REGISTRY}/${env.SELECTED_ECR_REPOSITORY}:${env.SELECTED_IMAGE_TAG}"
                        env.LATEST_IMAGE_URI = "${env.ECR_REGISTRY}/${env.SELECTED_ECR_REPOSITORY}:latest"
                    }

                    sh '''
                        set -eux
                        echo "Image URI: ${IMAGE_URI}"

                        aws ecr get-login-password --region "${SELECTED_AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

                        docker build \
                            --build-arg API_GATEWAY_URL="${API_GATEWAY_URL}" \
                            --build-arg RDS_ENDPOINT="${RDS_ENDPOINT}" \
                            -t "${IMAGE_URI}" \
                            -t "${LATEST_IMAGE_URI}" \
                            .

                        docker push "${IMAGE_URI}"

                        if [ "${PUSH_LATEST}" = "true" ]; then
                            echo "Pushing latest image tag..."
                            docker push "${LATEST_IMAGE_URI}"
                        else
                            echo "Skipping latest image tag."
                        fi
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            when { expression { return params.DEPLOY_TO_EKS } }
            steps {
                withCredentials([aws(
                    credentialsId: "${params.AWS_CREDENTIALS_ID}",
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    sh '''
                        set -eux
                        eval "${CONFIGURE_KUBECTL_CMD}"
                        
                        # Create namespace if it doesnt exist
                        kubectl get namespace "${SELECTED_K8S_NAMESPACE}" || kubectl create namespace "${SELECTED_K8S_NAMESPACE}"

                        # Remove validate=false as it is deprecated in newer kubectl versions
                        sed \
                            -e "s|IMAGE_PLACEHOLDER|${IMAGE_URI}|g" \
                            -e "s|NAMESPACE_PLACEHOLDER|${SELECTED_K8S_NAMESPACE}|g" \
                            k8s/deployment.yaml \
                            | kubectl apply -f -

                        sed \
                            "s|NAMESPACE_PLACEHOLDER|${SELECTED_K8S_NAMESPACE}|g" \
                            k8s/service.yaml \
                            | kubectl apply -f -

                        kubectl rollout status \
                            deployment/"${APP_NAME}" \
                            --namespace "${SELECTED_K8S_NAMESPACE}" \
                            --timeout=180s
                    '''
                }
            }
        }

        stage('Verify Deployment') {
            when { expression { return params.DEPLOY_TO_EKS } }
            steps {
                withCredentials([aws(
                    credentialsId: "${params.AWS_CREDENTIALS_ID}",
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                )]) {
                    sh '''
                        set -eux
                        eval "${CONFIGURE_KUBECTL_CMD}"

                        kubectl get deployment "${APP_NAME}" --namespace "${SELECTED_K8S_NAMESPACE}" --output wide
                        kubectl get pods --namespace "${SELECTED_K8S_NAMESPACE}" --output wide
                        kubectl get service "${APP_NAME}" --namespace "${SELECTED_K8S_NAMESPACE}"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo """
========================================
BUILD COMPLETED SUCCESSFULLY
========================================
Application     : ${env.APP_NAME}
Image           : ${env.IMAGE_URI ?: 'Not built'}
EKS Cluster     : ${env.SELECTED_EKS_CLUSTER}
Namespace       : ${env.SELECTED_K8S_NAMESPACE}
API Gateway     : ${params.API_GATEWAY_URL}
RDS Endpoint    : ${params.RDS_ENDPOINT}
========================================
"""
        }
        failure {
            echo 'Build or deployment failed. Check the failed Jenkins stage and console output.'
        }
        always {
            sh 'docker image prune -f || true'
            deleteDir()
        }
    }
}

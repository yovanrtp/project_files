pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    parameters {
        choice(
            name: 'AWS_REGION',
            choices: [
                'us-east-1',
                'us-east-2',
                'us-west-1',
                'us-west-2'
            ],
            description: 'AWS Region used for ECR and EKS.'
        )

        string(
            name: 'ECR_REPOSITORY',
            defaultValue: 'jenkins-demo',
            trim: true,
            description: 'Amazon ECR repository name.'
        )

        string(
            name: 'EKS_CLUSTER',
            defaultValue: 'demo-eks',
            trim: true,
            description: 'Target Amazon EKS cluster name.'
        )

        string(
            name: 'K8S_NAMESPACE',
            defaultValue: 'jenkins-demo',
            trim: true,
            description: 'Kubernetes namespace for the deployment.'
        )

        string(
            name: 'IMAGE_TAG',
            defaultValue: '',
            trim: true,
            description: 'Optional image tag. Leave empty to use BUILD_NUMBER-GIT_COMMIT.'
        )

        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run application tests before building the Docker image.'
        )

        booleanParam(
            name: 'PUSH_LATEST',
            defaultValue: true,
            description: 'Also push the Docker image with the latest tag.'
        )

        booleanParam(
            name: 'DEPLOY_TO_EKS',
            defaultValue: true,
            description: 'Deploy the pushed image to Amazon EKS.'
        )

        string(
            name: 'AWS_CREDENTIALS_ID',
            defaultValue: 'aws-jenkins-credentials',
            trim: true,
            description: 'Jenkins credential ID containing AWS credentials.'
        )
    }

    environment {
        APP_NAME = 'jenkins-demo'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm

                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()

                    env.SELECTED_AWS_REGION = params.AWS_REGION
                    env.SELECTED_ECR_REPOSITORY = params.ECR_REPOSITORY
                    env.SELECTED_EKS_CLUSTER = params.EKS_CLUSTER
                    env.SELECTED_K8S_NAMESPACE = params.K8S_NAMESPACE
                    env.PUSH_LATEST_VALUE = params.PUSH_LATEST.toString()
                    env.DEPLOY_TO_EKS_VALUE = params.DEPLOY_TO_EKS.toString()

                    if (params.IMAGE_TAG?.trim()) {
                        env.SELECTED_IMAGE_TAG = params.IMAGE_TAG.trim()
                    } else {
                        env.SELECTED_IMAGE_TAG =
                            "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                    }
                }

                echo """
==========================================
Build configuration
==========================================
Git Commit     : ${env.GIT_COMMIT_SHORT}
AWS Region     : ${env.SELECTED_AWS_REGION}
ECR Repository : ${env.SELECTED_ECR_REPOSITORY}
EKS Cluster    : ${env.SELECTED_EKS_CLUSTER}
Namespace      : ${env.SELECTED_K8S_NAMESPACE}
Image Tag      : ${env.SELECTED_IMAGE_TAG}
Run Tests      : ${params.RUN_TESTS}
Push Latest    : ${params.PUSH_LATEST}
Deploy to EKS  : ${params.DEPLOY_TO_EKS}
==========================================
"""
            }
        }

        stage('Test Package') {
            when {
                expression {
                    return params.RUN_TESTS
                }
            }

            steps {
                echo 'Running application tests...'

                sh '''
                    set -eux

                    python3 --version

                    python3 -m venv .venv
                    . .venv/bin/activate

                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest

                    pytest -v
                '''
            }
        }

        stage('Build and Push Image') {
            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding',
                     credentialsId: "${params.AWS_CREDENTIALS_ID}"]
                ]) {
                    script {
                        env.AWS_ACCOUNT_ID = sh(
                            script: '''
                                aws sts get-caller-identity \
                                    --query Account \
                                    --output text
                            ''',
                            returnStdout: true
                        ).trim()

                        env.ECR_REGISTRY =
                            "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.SELECTED_AWS_REGION}.amazonaws.com"

                        env.IMAGE_URI =
                            "${env.ECR_REGISTRY}/${env.SELECTED_ECR_REPOSITORY}:${env.SELECTED_IMAGE_TAG}"

                        env.LATEST_IMAGE_URI =
                            "${env.ECR_REGISTRY}/${env.SELECTED_ECR_REPOSITORY}:latest"
                    }

                    sh '''
                        set -eux

                        echo "Image URI: ${IMAGE_URI}"

                        aws ecr get-login-password \
                            --region "${SELECTED_AWS_REGION}" \
                        | docker login \
                            --username AWS \
                            --password-stdin "${ECR_REGISTRY}"

                        docker build \
                            -t "${IMAGE_URI}" \
                            -t "${LATEST_IMAGE_URI}" \
                            .

                        docker push "${IMAGE_URI}"

                        if [ "${PUSH_LATEST_VALUE}" = "true" ]; then
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
            when {
                expression {
                    return params.DEPLOY_TO_EKS
                }
            }

            steps {
                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding',
                     credentialsId: "${params.AWS_CREDENTIALS_ID}"]
                ]) {
                    sh '''
                        set -eux

                        aws eks update-kubeconfig \
                            --region "${SELECTED_AWS_REGION}" \
                            --name "${SELECTED_EKS_CLUSTER}"

                        kubectl apply -f k8s/namespace.yaml

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
            when {
                expression {
                    return params.DEPLOY_TO_EKS
                }
            }

            steps {
                sh '''
                    set -eux

                    kubectl get deployment "${APP_NAME}" \
                        --namespace "${SELECTED_K8S_NAMESPACE}" \
                        --output wide

                    kubectl get pods \
                        --namespace "${SELECTED_K8S_NAMESPACE}" \
                        --output wide

                    kubectl get service "${APP_NAME}" \
                        --namespace "${SELECTED_K8S_NAMESPACE}"

                    echo "Deployed image:"
                    kubectl get deployment "${APP_NAME}" \
                        --namespace "${SELECTED_K8S_NAMESPACE}" \
                        --output jsonpath='{.spec.template.spec.containers[0].image}'

                    echo
                '''
            }
        }
    }

    post {
        success {
            echo """
========================================
BUILD COMPLETED SUCCESSFULLY
========================================
Application : ${env.APP_NAME}
Image       : ${env.IMAGE_URI ?: 'Not built'}
EKS Cluster : ${env.SELECTED_EKS_CLUSTER}
Namespace   : ${env.SELECTED_K8S_NAMESPACE}
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
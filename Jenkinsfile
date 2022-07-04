pipeline {
    agent {
        label 'tooling'
    }

    triggers {
        githubPush()
    }

    environment {
        // General variables
        ACCOUNT_ID = "398692602192"
        REGION = "ap-southeast-1"
        APPS_ORG = "pids-applications"
        DEVOPS_ORG = "pids-devops"
        GITHUB_CREDENTIALS = credentials('github')

        // Service variables
        SERVICE_NAME = "process-service"
        APP_REPO = "git@github.com:${APPS_ORG}/${SERVICE_NAME}.git"
        DEVOPS_REPO = "git@github.com:${DEVOPS_ORG}/${SERVICE_NAME}.git"
        ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
        IMAGE_REPO = "${ECR_URI}/${SERVICE_NAME}"
        IMAGE_TAG = "${BUILD_ID}"
        CONTAINER_IMAGE =  "${IMAGE_REPO}:${IMAGE_TAG}"

        NAMESPACE = "default"
        SQS_SA = "sqs-processing-sa"
        SQS_ROLE = "arn:aws:iam::808059214513:role/sqs-processing-sa"
        AWS_REGION = "ap-southeast-1"
        QUEUE_URL = "https://sqs.ap-southeast-1.amazonaws.com/808059214513/pids-prod-sqs"
        PSQL_USER = "dbadmin"
        PSQL_PASSWORD = "dbpassword11"
        PSQL_HOST = "pids-db.csqxvg6p6diw.ap-southeast-1.rds.amazonaws.com"
        PSQL_PORT = "5432"
        PSQL_DATABASE = "pidsuser"
    }

    stages {
        stage('Preparation') {
            steps {
                echo "Login to ECR.."
                sh '''
                    set +x
                    REPO_LOGIN_PWD=$(aws ecr get-login-password --region ap-southeast-1)
                    docker login -u AWS -p $REPO_LOGIN_PWD $ECR_URI
                '''
            }
        }

        stage('Build and Deploy Image ') {
            steps {
                sh '''
                    docker build -t $IMAGE_REPO:$IMAGE_TAG .
                    docker push $IMAGE_REPO:$IMAGE_TAG
                '''
                echo 'Finished pushing image ${IMAGE_REPO}:${IMAGE_TAG} to ECR repo test'
            }
        }

        stage('Checkout Devops Repo') {
            steps {
                dir('devops') {
                    git branch: "main", credentialsId: "github-key", url: "${DEVOPS_REPO}"
                }
                sh '''
                    ls ./devops
                '''
            }
        }

        stage('Update and Push Devops Repo') {
            steps {
                sh '''
                    cd ${WORKSPACE}/devops/
                    envsubst < ./deployment.tpl.yaml > ./deployment.yaml
                    cat ${WORKSPACE}/devops/deployment.yaml
                '''
                sshagent (credentials: ['github-key']) {
                    sh '''
                        cd ${WORKSPACE}/devops/
                        git config user.email "tranvanloc412@gmail.com"
                        git config user.name "Loc Tran"
                        git add .
                        git commit -m "jenkins build no ${BUILD_ID} updates manifest files"
                        git push --set-upstream origin main
                    '''
                }
            }
        }

        stage('Clean App Workspace') {
            steps {
                cleanWs()
            }
        }
    }
}

pipeline {
    agent {
        docker {
            image 'python:3.9'  // Use the base image your project needs
        }
    }
    stages {
        stage('Clone Repository') {
            steps {
                git 'https://github.com/Dineshraja62005/video-to-audio-converter.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t video-to-audio-converter .'
            }
        }
        stage('Run Tests') {
            steps {
                sh 'docker run --rm video-to-audio-converter pytest tests/'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker run -d -p 5000:5000 video-to-audio-converter'
            }
        }
    }
}

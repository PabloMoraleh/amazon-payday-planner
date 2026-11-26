pipeline {
    agent any

    triggers {
        cron('H 8 1-5 * *')
    }

    environment {
        APP_ENV = 'test'
        SECRET_KEY = 'jenkins-test-only-secret'
        SUPABASE_URL = 'https://example.supabase.co'
        SUPABASE_PUBLISHABLE_KEY = 'test-publishable-key'
    }

    stages {
        stage('Install dependencies') {
            steps {
                sh 'python3 -c "import sys; print(sys.version); assert sys.version_info >= (3, 11)"'
                sh 'python3 -m venv .venv'
                sh '.venv/bin/python -m pip install --upgrade pip'
                sh '.venv/bin/pip install -r requirements.txt'
            }
        }

        stage('Compile translations') {
            steps {
                sh '.venv/bin/pybabel compile -d translations --statistics'
            }
        }

        stage('Run tests') {
            steps {
                sh '.venv/bin/python -m pytest -q'
            }
        }

        stage('Send monthly browser reminders') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([
                    string(credentialsId: 'prod-supabase-url', variable: 'SUPABASE_URL'),
                    string(credentialsId: 'prod-supabase-service-role-key', variable: 'SUPABASE_SERVICE_ROLE_KEY'),
                    string(credentialsId: 'vapid-private-key', variable: 'VAPID_PRIVATE_KEY'),
                    string(credentialsId: 'vapid-subject', variable: 'VAPID_SUBJECT')
                ]) {
                    sh '.venv/bin/python scripts/send_monthly_notifications.py'
                }
            }
        }
    }
}

#!/usr/bin/env python
"""
Django Fleet Management System Setup Script
"""

import os
import sys
import subprocess
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🔧 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_django_installation():
    """Check if Django is installed"""
    try:
        import django
        print(f"✅ Django {django.get_version()} is installed")
        return True
    except ImportError:
        print("❌ Django is not installed")
        return False

def setup_environment():
    """Set up the Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings')
    django.setup()

def main():
    """Main setup function"""
    print("🚛 Django Fleet Management System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install requirements. Please check your internet connection and try again.")
        sys.exit(1)
    
    # Check Django installation
    if not check_django_installation():
        sys.exit(1)
    
    # Set up Django environment
    setup_environment()
    
    # Run migrations
    if not run_command("python manage.py makemigrations", "Creating database migrations"):
        print("❌ Failed to create migrations")
        sys.exit(1)
    
    if not run_command("python manage.py migrate", "Applying database migrations"):
        print("❌ Failed to apply migrations")
        sys.exit(1)
    
    # Collect static files
    if not run_command("python manage.py collectstatic --noinput", "Collecting static files"):
        print("⚠️  Warning: Failed to collect static files, but continuing...")
    
    print("\n" + "="*50)
    print("🎉 Setup completed successfully!")
    print("="*50)
    print("\n📋 Next steps:")
    print("1. Create a superuser account:")
    print("   python manage.py createsuperuser")
    print("\n2. Start the development server:")
    print("   python manage.py runserver")
    print("\n3. Open your browser and go to:")
    print("   http://127.0.0.1:8000/")
    print("\n4. Access the admin panel at:")
    print("   http://127.0.0.1:8000/admin/")
    print("\n💡 For production deployment, see README.md")

if __name__ == "__main__":
    main()
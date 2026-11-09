#!/bin/bash
# Django Fleet Management System - Unix/Linux/macOS Script
# This script helps Unix-based users manage the Django application easily

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Function to print header
print_header() {
    clear
    print_color $BLUE "========================================================"
    print_color $BLUE "         Django Fleet Management System"
    print_color $BLUE "========================================================"
    echo
}

# Function to pause
pause() {
    read -p "Press [Enter] to continue..."
}

# Main menu function
show_menu() {
    print_header
    echo "Please select an option:"
    echo
    echo "1. Install Dependencies (First Time Setup)"
    echo "2. Run Database Migrations"
    echo "3. Create Superuser Account"
    echo "4. Start Development Server"
    echo "5. Collect Static Files"
    echo "6. Open Django Shell"
    echo "7. Run Tests"
    echo "8. Check System Status"
    echo "9. Exit"
    echo
}

# Install dependencies
install_deps() {
    print_header
    print_color $YELLOW "Installing dependencies..."
    
    if pip install -r requirements.txt; then
        print_color $GREEN "Dependencies installed successfully!"
        echo
        print_color $YELLOW "Running initial migrations..."
        python manage.py migrate
        print_color $GREEN "Setup complete! You can now create a superuser account."
    else
        print_color $RED "Error installing dependencies!"
    fi
    pause
}

# Run migrations
run_migrations() {
    print_header
    print_color $YELLOW "Running database migrations..."
    
    python manage.py makemigrations
    if python manage.py migrate; then
        print_color $GREEN "Migrations completed successfully!"
    else
        print_color $RED "Error running migrations!"
    fi
    pause
}

# Create superuser
create_superuser() {
    print_header
    print_color $YELLOW "Creating superuser account..."
    python manage.py createsuperuser
    pause
}

# Start development server
start_server() {
    print_header
    print_color $YELLOW "Starting Django development server..."
    echo
    print_color $GREEN "The server will start at: http://127.0.0.1:8000/"
    print_color $GREEN "Admin panel: http://127.0.0.1:8000/admin/"
    echo
    print_color $YELLOW "Press Ctrl+C to stop the server"
    echo
    python manage.py runserver
    pause
}

# Collect static files
collect_static() {
    print_header
    print_color $YELLOW "Collecting static files..."
    python manage.py collectstatic
    pause
}

# Open Django shell
open_shell() {
    print_header
    print_color $YELLOW "Opening Django shell..."
    python manage.py shell
    pause
}

# Run tests
run_tests() {
    print_header
    print_color $YELLOW "Running tests..."
    python manage.py test
    pause
}

# Check system status
check_status() {
    print_header
    print_color $YELLOW "Checking system status..."
    echo
    
    # Check Python version
    print_color $BLUE "Python version:"
    python --version
    echo
    
    # Check Django installation
    print_color $BLUE "Django version:"
    python -c "import django; print(django.get_version())" 2>/dev/null || print_color $RED "Django not installed"
    echo
    
    # Check database
    print_color $BLUE "Database status:"
    python manage.py check --database default
    echo
    
    # Check for migrations
    print_color $BLUE "Migration status:"
    python manage.py showmigrations
    echo
    
    pause
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (1-9): " choice
    
    case $choice in
        1) install_deps ;;
        2) run_migrations ;;
        3) create_superuser ;;
        4) start_server ;;
        5) collect_static ;;
        6) open_shell ;;
        7) run_tests ;;
        8) check_status ;;
        9) 
            print_color $GREEN "Thank you for using Django Fleet Management System!"
            exit 0
            ;;
        *)
            print_color $RED "Invalid choice. Please try again."
            pause
            ;;
    esac
done
#!/bin/bash

# Brazilian Boleto Number Extractor - Shell Script Wrapper
# This script makes it easier to run the boleto extractor

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Brazilian Boleto Number Extractor"
    echo "================================="
    echo ""
    echo "Usage: $0 <pdf_file> [options]"
    echo ""
    echo "Options:"
    echo "  --verbose, -v    Enable verbose logging"
    echo "  --format, -f     Format output with spaces"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 boleto.pdf"
    echo "  $0 boleto.pdf --format"
    echo "  $0 boleto.pdf --verbose --format"
    echo ""
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        print_success "Virtual environment created"
    fi
}

# Function to install dependencies
install_dependencies() {
    if [ ! -f "venv/pyvenv.cfg" ]; then
        print_error "Virtual environment is corrupted. Please delete 'venv' folder and run again."
        exit 1
    fi
    
    print_info "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies"
        exit 1
    fi
    print_success "Dependencies installed"
}

# Function to check if zbar is installed
check_zbar() {
    if ! command -v zbarimg &> /dev/null; then
        print_warning "zbar not found. Barcode scanning may not work properly."
        print_info "To install zbar:"
        echo "  macOS: brew install zbar"
        echo "  Ubuntu/Debian: sudo apt-get install libzbar0"
        echo "  Windows: Download from https://github.com/NaturalHistoryMuseum/pyzbar/releases"
        echo ""
    fi
}

# Main script
main() {
    # Check if help is requested
    if [[ "$1" == "--help" || "$1" == "-h" || -z "$1" ]]; then
        show_usage
        exit 0
    fi
    
    # Get the PDF file path (first argument)
    PDF_FILE="$1"
    shift  # Remove the first argument
    
    # Check if PDF file exists
    if [ ! -f "$PDF_FILE" ]; then
        print_error "PDF file not found: $PDF_FILE"
        exit 1
    fi
    
    # Check if it's a PDF file
    if [[ ! "$PDF_FILE" =~ \.pdf$ ]]; then
        print_error "File is not a PDF: $PDF_FILE"
        exit 1
    fi
    
    print_info "Processing PDF: $PDF_FILE"
    
    # Check and setup environment
    check_venv
    install_dependencies
    check_zbar
    
    # Build the command
    CMD="source venv/bin/activate && python boleto_extractor.py \"$PDF_FILE\""
    
    # Add options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose|-v)
                CMD="$CMD --verbose"
                shift
                ;;
            --format|-f)
                CMD="$CMD --format"
                shift
                ;;
            *)
                print_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Run the extractor
    print_info "Running boleto extractor..."
    echo ""
    eval $CMD
    
    if [ $? -eq 0 ]; then
        print_success "Extraction completed"
    else
        print_error "Extraction failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 
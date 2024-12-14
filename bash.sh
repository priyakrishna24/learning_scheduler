#!/bin/bash

# Create a temporary directory for the package
mkdir -p package

# Install dependencies to the package directory
pip install -r requirements.txt --target ./package

# Copy your source code to the package directory
cp -r src/* package/

# Create the ZIP file
cd package
zip -r ../deployment-package.zip .
cd ..

# Clean up
rm -rf package

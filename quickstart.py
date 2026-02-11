#!/usr/bin/env python3
"""
Quick Start Script for Kumbh Smart Seva v2
Executes the complete setup in the correct order
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n📌 {description}...")
    print(f"   Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Success!")
            return True
        else:
            print(f"❌ Failed!")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main quick start"""
    print("\n" + "="*70)
    print("🏛️  KUMBH SMART SEVA v2 - QUICK START GUIDE")
    print("="*70)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    steps = [
        ("python setup.py", "Step 1: Initialize Database and Verify Setup"),
        ("python init_sample_data.py", "Step 2: Insert Sample Data"),
        ("python test_system.py", "Step 3: Run Tests"),
    ]
    
    print("\n📋 This script will execute the following steps:")
    for i, (cmd, desc) in enumerate(steps, 1):
        print(f"   {i}. {desc}")
    
    print("\n" + "="*70)
    
    all_passed = True
    for cmd, description in steps:
        if not run_command(cmd, description):
            all_passed = False
            print("\n⚠️  Continuing despite error...")
    
    # Final instructions
    print("\n" + "="*70)
    print("🚀 SETUP COMPLETE!")
    print("="*70)
    
    if all_passed:
        print("\n✅ All steps completed successfully!")
    else:
        print("\n⚠️  Some steps encountered issues. Please review above.")
    
    print("\n📝 To start the application:")
    print("   1. Make sure all requirements are installed:")
    print("      pip install -r requirements.txt")
    print("   2. Run the application:")
    print("      python app.py")
    print("   3. Open in browser:")
    print("      http://localhost:5000")
    
    print("\n🔐 Test Credentials:")
    print("   Regular User:")
    print("      Email: rajesh@example.com")
    print("      Password: password123")
    print("   Admin:")
    print("      Email: admin@kumbh.com")
    print("      Password: admin123")
    print("   Supervisor:")
    print("      Email: supervisor@kumbh.com")
    print("      Password: admin123")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()

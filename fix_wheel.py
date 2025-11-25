#!/usr/bin/env python3
import zipfile
import tempfile
import shutil
import os
import sys

def fix_wheel(wheel_path):
    """Remove 'Dynamic: license-file' from wheel metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract wheel
        with zipfile.ZipFile(wheel_path, 'r') as zf:
            zf.extractall(tmpdir)
        
        # Find and fix METADATA file
        for root, dirs, files in os.walk(tmpdir):
            if 'METADATA' in files:
                metadata_path = os.path.join(root, 'METADATA')
                with open(metadata_path, 'r') as f:
                    lines = f.readlines()
                
                # Remove Dynamic: license-file and License-File lines
                fixed_lines = [line for line in lines 
                              if not line.startswith('Dynamic: license-file') 
                              and not line.startswith('License-File:')]
                
                with open(metadata_path, 'w') as f:
                    f.writelines(fixed_lines)
                break
        
        # Repack wheel
        backup_path = wheel_path + '.backup'
        shutil.move(wheel_path, backup_path)
        
        with zipfile.ZipFile(wheel_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)
        
        os.remove(backup_path)
        print(f"Fixed {wheel_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix_wheel.py <wheel_file>")
        sys.exit(1)
    
    fix_wheel(sys.argv[1])

#!/usr/bin/env python3
import tarfile
import tempfile
import shutil
import os
import sys

def fix_sdist(sdist_path):
    """Remove 'Dynamic: license-file' and 'License-File' from sdist metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract sdist
        with tarfile.open(sdist_path, 'r:gz') as tf:
            tf.extractall(tmpdir)
        
        # Find and fix PKG-INFO file
        for root, dirs, files in os.walk(tmpdir):
            if 'PKG-INFO' in files:
                pkg_info_path = os.path.join(root, 'PKG-INFO')
                with open(pkg_info_path, 'r') as f:
                    lines = f.readlines()
                
                # Remove Dynamic: license-file and License-File lines
                fixed_lines = [line for line in lines 
                              if not line.startswith('Dynamic: license-file') 
                              and not line.startswith('License-File:')]
                
                with open(pkg_info_path, 'w') as f:
                    f.writelines(fixed_lines)
        
        # Repack sdist
        backup_path = sdist_path + '.backup'
        shutil.move(sdist_path, backup_path)
        
        # Get the top-level directory name
        top_dir = os.listdir(tmpdir)[0]
        top_path = os.path.join(tmpdir, top_dir)
        
        with tarfile.open(sdist_path, 'w:gz') as tf:
            tf.add(top_path, arcname=top_dir)
        
        os.remove(backup_path)
        print(f"Fixed {sdist_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix_sdist.py <sdist_file>")
        sys.exit(1)
    
    fix_sdist(sys.argv[1])

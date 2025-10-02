import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import zipfile
import tarfile

class IsoManager:
    def __init__(self):
        self.mounted_isos = {}
        self.temp_directory = tempfile.mkdtemp(prefix="detorrent_iso_")
        
    def scan_directory(self, directory: str) -> List[Dict]:
        iso_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return iso_files
        
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and self._is_iso_file(file_path):
                iso_info = self._extract_iso_info(file_path)
                iso_files.append(iso_info)
        
        return iso_files
    
    def _is_iso_file(self, file_path: Path) -> bool:
        iso_extensions = ['.iso', '.img', '.dmg', '.vdi', '.vmdk']
        return file_path.suffix.lower() in iso_extensions
    
    def _extract_iso_info(self, file_path: Path) -> Dict:
        try:
            stat_info = file_path.stat()
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'checksum': self._calculate_checksum(file_path)
            }
        except Exception as e:
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': 0,
                'modified': 0,
                'error': str(e)
            }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def validate_iso_file(self, iso_path: str) -> Dict:
        try:
            if not os.path.exists(iso_path):
                return {'valid': False, 'error': 'File does not exist'}
            
            file_size = os.path.getsize(iso_path)
            if file_size < 1024 * 1024:
                return {'valid': False, 'error': 'File too small to be valid ISO'}
            
            if not self._verify_iso_structure(iso_path):
                return {'valid': False, 'error': 'Invalid ISO structure'}
            
            return {'valid': True, 'size': file_size}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _verify_iso_structure(self, iso_path: str) -> bool:
        try:
            with open(iso_path, 'rb') as f:
                header = f.read(2048)
                if len(header) < 2048:
                    return False
                
                if header[0:5] == b'CD001':
                    return True
                
                if header[0:4] == b'\x00\x00\x00\x00':
                    return True
                
                return False
        except Exception:
            return False
    
    def mount_iso(self, iso_path: str) -> Dict:
        try:
            mount_point = os.path.join(self.temp_directory, f"mount_{len(self.mounted_isos)}")
            os.makedirs(mount_point, exist_ok=True)
            
            if os.name == 'nt':
                result = subprocess.run([
                    'powershell', '-Command',
                    f'Mount-DiskImage -ImagePath "{iso_path}" -PassThru | Get-Volume | Get-Partition | Add-PartitionAccessPath -AccessPath "{mount_point}"'
                ], capture_output=True, text=True)
            else:
                result = subprocess.run([
                    'sudo', 'mount', '-o', 'loop', iso_path, mount_point
                ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.mounted_isos[iso_path] = mount_point
                return {'success': True, 'mount_point': mount_point}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unmount_iso(self, iso_path: str) -> Dict:
        try:
            if iso_path not in self.mounted_isos:
                return {'success': False, 'error': 'ISO not mounted'}
            
            mount_point = self.mounted_isos[iso_path]
            
            if os.name == 'nt':
                result = subprocess.run([
                    'powershell', '-Command',
                    f'Dismount-DiskImage -ImagePath "{iso_path}"'
                ], capture_output=True, text=True)
            else:
                result = subprocess.run([
                    'sudo', 'umount', mount_point
                ], capture_output=True, text=True)
            
            if result.returncode == 0:
                del self.mounted_isos[iso_path]
                shutil.rmtree(mount_point, ignore_errors=True)
                return {'success': True}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_from_mounted(self, mount_point: str, target_partition: str) -> Dict:
        try:
            install_script = self._find_install_script(mount_point)
            if not install_script:
                return {'success': False, 'error': 'No installation script found'}
            
            if os.name == 'nt':
                result = subprocess.run([
                    'powershell', '-Command',
                    f'Start-Process -FilePath "{install_script}" -ArgumentList "/s /t:{target_partition}" -Wait'
                ], capture_output=True, text=True)
            else:
                result = subprocess.run([
                    'sudo', 'bash', install_script, target_partition
                ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _find_install_script(self, mount_point: str) -> Optional[str]:
        possible_scripts = [
            'setup.exe',
            'install.exe',
            'autorun.exe',
            'install.sh',
            'setup.sh',
            'installer'
        ]
        
        for script in possible_scripts:
            script_path = os.path.join(mount_point, script)
            if os.path.exists(script_path):
                return script_path
        
        return None
    
    def cleanup(self):
        for iso_path in list(self.mounted_isos.keys()):
            self.unmount_iso(iso_path)
        
        if os.path.exists(self.temp_directory):
            shutil.rmtree(self.temp_directory, ignore_errors=True)

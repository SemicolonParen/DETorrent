import os
import subprocess
import platform
import re
from pathlib import Path
from typing import Dict, List, Optional
import json

class OsDetector:
    def __init__(self):
        self.os_signatures = {
            'windows': {
                'patterns': [r'windows', r'winnt', r'win32'],
                'files': ['bootmgr', 'ntldr', 'winload.exe'],
                'directories': ['Windows', 'Program Files']
            },
            'linux': {
                'patterns': [r'linux', r'ubuntu', r'debian', r'fedora', r'centos'],
                'files': ['vmlinuz', 'initrd.img', 'grub.cfg'],
                'directories': ['boot', 'etc', 'usr']
            },
            'macos': {
                'patterns': [r'macos', r'darwin', r'mac os'],
                'files': ['mach_kernel', 'boot.efi'],
                'directories': ['System', 'Applications']
            }
        }
    
    def analyze_system(self) -> Dict:
        try:
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version()
            }
            
            boot_info = self._get_boot_information()
            partition_info = self._get_partition_information()
            
            return {
                'system': system_info,
                'boot': boot_info,
                'partitions': partition_info,
                'detected_os': self._detect_current_os()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _detect_current_os(self) -> Dict:
        try:
            if os.name == 'nt':
                return self._detect_windows()
            elif os.name == 'posix':
                return self._detect_unix_like()
            else:
                return {'name': 'unknown', 'version': 'unknown'}
        except Exception as e:
            return {'name': 'unknown', 'version': 'unknown', 'error': str(e)}
    
    def _detect_windows(self) -> Dict:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'Get-WmiObject -Class Win32_OperatingSystem | Select-Object Caption, Version'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Caption' in line:
                        name = line.split(':')[1].strip()
                    elif 'Version' in line:
                        version = line.split(':')[1].strip()
                
                return {'name': name, 'version': version}
            else:
                return {'name': 'Windows', 'version': 'Unknown'}
                
        except Exception as e:
            return {'name': 'Windows', 'version': 'Unknown', 'error': str(e)}
    
    def _detect_unix_like(self) -> Dict:
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                
                name_match = re.search(r'NAME="([^"]+)"', content)
                version_match = re.search(r'VERSION="([^"]+)"', content)
                
                name = name_match.group(1) if name_match else 'Linux'
                version = version_match.group(1) if version_match else 'Unknown'
                
                return {'name': name, 'version': version}
            else:
                return {'name': 'Unix-like', 'version': 'Unknown'}
                
        except Exception as e:
            return {'name': 'Unix-like', 'version': 'Unknown', 'error': str(e)}
    
    def _get_boot_information(self) -> Dict:
        try:
            if os.name == 'nt':
                return self._get_windows_boot_info()
            else:
                return self._get_unix_boot_info()
        except Exception as e:
            return {'error': str(e)}
    
    def _get_windows_boot_info(self) -> Dict:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'bcdedit /enum firmware'
            ], capture_output=True, text=True)
            
            boot_info = {
                'bootloader': 'Windows Boot Manager',
                'entries': []
            }
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'description' in line.lower():
                        boot_info['entries'].append(line.strip())
            
            return boot_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_unix_boot_info(self) -> Dict:
        try:
            boot_info = {
                'bootloader': 'GRUB',
                'config_path': '/etc/default/grub',
                'entries': []
            }
            
            if os.path.exists('/etc/default/grub'):
                with open('/etc/default/grub', 'r') as f:
                    content = f.read()
                
                default_match = re.search(r'GRUB_DEFAULT="([^"]+)"', content)
                if default_match:
                    boot_info['default_entry'] = default_match.group(1)
            
            return boot_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_partition_information(self) -> List[Dict]:
        try:
            if os.name == 'nt':
                return self._get_windows_partitions()
            else:
                return self._get_unix_partitions()
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_windows_partitions(self) -> List[Dict]:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'Get-Partition | Select-Object PartitionNumber, DriveLetter, Size, Type'
            ], capture_output=True, text=True)
            
            partitions = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[2:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            partitions.append({
                                'number': parts[0],
                                'letter': parts[1],
                                'size': parts[2],
                                'type': parts[3]
                            })
            
            return partitions
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_unix_partitions(self) -> List[Dict]:
        try:
            result = subprocess.run([
                'lsblk', '-f', '-J'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                partitions = []
                
                for device in data.get('blockdevices', []):
                    if device.get('type') == 'part':
                        partitions.append({
                            'name': device.get('name', ''),
                            'fstype': device.get('fstype', ''),
                            'size': device.get('size', ''),
                            'mountpoint': device.get('mountpoint', '')
                        })
                
                return partitions
            else:
                return []
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def extract_os_info(self, iso_path: str) -> Dict:
        try:
            mount_point = self._mount_iso_temporarily(iso_path)
            if not mount_point:
                return {'error': 'Failed to mount ISO'}
            
            os_info = self._analyze_mounted_iso(mount_point)
            self._unmount_iso_temporarily(mount_point)
            
            return os_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _mount_iso_temporarily(self, iso_path: str) -> Optional[str]:
        try:
            import tempfile
            mount_point = tempfile.mkdtemp(prefix="detorrent_os_detect_")
            
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
                return mount_point
            else:
                return None
                
        except Exception:
            return None
    
    def _unmount_iso_temporarily(self, mount_point: str):
        try:
            if os.name == 'nt':
                subprocess.run([
                    'powershell', '-Command',
                    f'Dismount-DiskImage -ImagePath "{mount_point}"'
                ], capture_output=True, text=True)
            else:
                subprocess.run([
                    'sudo', 'umount', mount_point
                ], capture_output=True, text=True)
            
            import shutil
            shutil.rmtree(mount_point, ignore_errors=True)
            
        except Exception:
            pass
    
    def _analyze_mounted_iso(self, mount_point: str) -> Dict:
        try:
            os_info = {
                'name': 'Unknown',
                'version': 'Unknown',
                'architecture': 'Unknown',
                'type': 'Unknown'
            }
            
            for os_type, signatures in self.os_signatures.items():
                if self._matches_signatures(mount_point, signatures):
                    os_info['type'] = os_type
                    os_info.update(self._extract_version_info(mount_point, os_type))
                    break
            
            return os_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _matches_signatures(self, mount_point: str, signatures: Dict) -> bool:
        try:
            for pattern in signatures['patterns']:
                if self._search_in_directory(mount_point, pattern, regex=True):
                    return True
            
            for file_name in signatures['files']:
                if self._search_in_directory(mount_point, file_name, regex=False):
                    return True
            
            for dir_name in signatures['directories']:
                if os.path.exists(os.path.join(mount_point, dir_name)):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _search_in_directory(self, directory: str, pattern: str, regex: bool = False) -> bool:
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if regex:
                        if re.search(pattern, file, re.IGNORECASE):
                            return True
                    else:
                        if pattern.lower() in file.lower():
                            return True
            return False
        except Exception:
            return False
    
    def _extract_version_info(self, mount_point: str, os_type: str) -> Dict:
        try:
            version_info = {}
            
            if os_type == 'windows':
                version_info.update(self._extract_windows_version(mount_point))
            elif os_type == 'linux':
                version_info.update(self._extract_linux_version(mount_point))
            elif os_type == 'macos':
                version_info.update(self._extract_macos_version(mount_point))
            
            return version_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_windows_version(self, mount_point: str) -> Dict:
        try:
            version_info = {'name': 'Windows', 'version': 'Unknown'}
            
            for root, dirs, files in os.walk(mount_point):
                for file in files:
                    if file.lower() == 'setup.exe':
                        version_info['installer'] = os.path.join(root, file)
                        break
            
            return version_info
            
        except Exception:
            return {'name': 'Windows', 'version': 'Unknown'}
    
    def _extract_linux_version(self, mount_point: str) -> Dict:
        try:
            version_info = {'name': 'Linux', 'version': 'Unknown'}
            
            os_release_path = os.path.join(mount_point, 'etc', 'os-release')
            if os.path.exists(os_release_path):
                with open(os_release_path, 'r') as f:
                    content = f.read()
                
                name_match = re.search(r'NAME="([^"]+)"', content)
                version_match = re.search(r'VERSION="([^"]+)"', content)
                
                if name_match:
                    version_info['name'] = name_match.group(1)
                if version_match:
                    version_info['version'] = version_match.group(1)
            
            return version_info
            
        except Exception:
            return {'name': 'Linux', 'version': 'Unknown'}
    
    def _extract_macos_version(self, mount_point: str) -> Dict:
        try:
            version_info = {'name': 'macOS', 'version': 'Unknown'}
            
            system_version_path = os.path.join(mount_point, 'System', 'Library', 'CoreServices', 'SystemVersion.plist')
            if os.path.exists(system_version_path):
                version_info['version_file'] = system_version_path
            
            return version_info
            
        except Exception:
            return {'name': 'macOS', 'version': 'Unknown'}

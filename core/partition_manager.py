import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import json

class PartitionManager:
    def __init__(self):
        self.partition_cache = {}
        self.operation_log = []
        
    def list_partitions(self) -> List[Dict]:
        try:
            if os.name == 'nt':
                return self._list_windows_partitions()
            else:
                return self._list_unix_partitions()
        except Exception as e:
            return [{'error': str(e)}]
    
    def _list_windows_partitions(self) -> List[Dict]:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'Get-Partition | Select-Object PartitionNumber, DriveLetter, Size, Type, DiskNumber | ConvertTo-Json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                partitions = []
                
                for partition in data:
                    partitions.append({
                        'number': partition.get('PartitionNumber', 0),
                        'letter': partition.get('DriveLetter', ''),
                        'size': partition.get('Size', 0),
                        'type': partition.get('Type', ''),
                        'disk': partition.get('DiskNumber', 0)
                    })
                
                return partitions
            else:
                return []
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def _list_unix_partitions(self) -> List[Dict]:
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
                            'mountpoint': device.get('mountpoint', ''),
                            'label': device.get('label', ''),
                            'uuid': device.get('uuid', '')
                        })
                
                return partitions
            else:
                return []
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def prepare_partition(self, partition_identifier: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._prepare_windows_partition(partition_identifier)
            else:
                return self._prepare_unix_partition(partition_identifier)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _prepare_windows_partition(self, partition_identifier: str) -> Dict:
        try:
            commands = [
                f'Get-Partition -PartitionNumber {partition_identifier} | Set-Partition -IsActive $true',
                f'Format-Volume -DriveLetter {partition_identifier} -FileSystem NTFS -Confirm:$false'
            ]
            
            for command in commands:
                result = subprocess.run([
                    'powershell', '-Command', command
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'Command failed: {result.stderr}'}
            
            self.operation_log.append(f'Prepared Windows partition {partition_identifier}')
            return {'success': True, 'message': f'Partition {partition_identifier} prepared'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _prepare_unix_partition(self, partition_identifier: str) -> Dict:
        try:
            commands = [
                f'sudo mkfs.ext4 -F {partition_identifier}',
                f'sudo mkdir -p /mnt/detorrent_install',
                f'sudo mount {partition_identifier} /mnt/detorrent_install'
            ]
            
            for command in commands:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'Command failed: {result.stderr}'}
            
            self.operation_log.append(f'Prepared Unix partition {partition_identifier}')
            return {'success': True, 'message': f'Partition {partition_identifier} prepared'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_partition(self, disk_identifier: str, size: str, partition_type: str = 'primary') -> Dict:
        try:
            if os.name == 'nt':
                return self._create_windows_partition(disk_identifier, size, partition_type)
            else:
                return self._create_unix_partition(disk_identifier, size, partition_type)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_windows_partition(self, disk_identifier: str, size: str, partition_type: str) -> Dict:
        try:
            command = f'New-Partition -DiskNumber {disk_identifier} -Size {size} -PartitionType {partition_type}'
            
            result = subprocess.run([
                'powershell', '-Command', command
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.operation_log.append(f'Created Windows partition on disk {disk_identifier}')
                return {'success': True, 'message': 'Partition created successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_unix_partition(self, disk_identifier: str, size: str, partition_type: str) -> Dict:
        try:
            commands = [
                f'sudo parted {disk_identifier} mkpart {partition_type} 0% 100%',
                f'sudo mkfs.ext4 -F {disk_identifier}1'
            ]
            
            for command in commands:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'Command failed: {result.stderr}'}
            
            self.operation_log.append(f'Created Unix partition on disk {disk_identifier}')
            return {'success': True, 'message': 'Partition created successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_partition(self, partition_identifier: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._delete_windows_partition(partition_identifier)
            else:
                return self._delete_unix_partition(partition_identifier)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _delete_windows_partition(self, partition_identifier: str) -> Dict:
        try:
            command = f'Remove-Partition -PartitionNumber {partition_identifier} -Confirm:$false'
            
            result = subprocess.run([
                'powershell', '-Command', command
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.operation_log.append(f'Deleted Windows partition {partition_identifier}')
                return {'success': True, 'message': 'Partition deleted successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _delete_unix_partition(self, partition_identifier: str) -> Dict:
        try:
            command = f'sudo parted {partition_identifier} rm 1'
            
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.operation_log.append(f'Deleted Unix partition {partition_identifier}')
                return {'success': True, 'message': 'Partition deleted successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def resize_partition(self, partition_identifier: str, new_size: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._resize_windows_partition(partition_identifier, new_size)
            else:
                return self._resize_unix_partition(partition_identifier, new_size)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _resize_windows_partition(self, partition_identifier: str, new_size: str) -> Dict:
        try:
            command = f'Resize-Partition -PartitionNumber {partition_identifier} -Size {new_size}'
            
            result = subprocess.run([
                'powershell', '-Command', command
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.operation_log.append(f'Resized Windows partition {partition_identifier}')
                return {'success': True, 'message': 'Partition resized successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _resize_unix_partition(self, partition_identifier: str, new_size: str) -> Dict:
        try:
            commands = [
                f'sudo parted {partition_identifier} resizepart 1 {new_size}',
                f'sudo resize2fs {partition_identifier}1'
            ]
            
            for command in commands:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'Command failed: {result.stderr}'}
            
            self.operation_log.append(f'Resized Unix partition {partition_identifier}')
            return {'success': True, 'message': 'Partition resized successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def format_partition(self, partition_identifier: str, filesystem: str = 'NTFS') -> Dict:
        try:
            if os.name == 'nt':
                return self._format_windows_partition(partition_identifier, filesystem)
            else:
                return self._format_unix_partition(partition_identifier, filesystem)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_windows_partition(self, partition_identifier: str, filesystem: str) -> Dict:
        try:
            command = f'Format-Volume -DriveLetter {partition_identifier} -FileSystem {filesystem} -Confirm:$false'
            
            result = subprocess.run([
                'powershell', '-Command', command
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.operation_log.append(f'Formatted Windows partition {partition_identifier}')
                return {'success': True, 'message': 'Partition formatted successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_unix_partition(self, partition_identifier: str, filesystem: str) -> Dict:
        try:
            command = f'sudo mkfs.{filesystem.lower()} -F {partition_identifier}'
            
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.operation_log.append(f'Formatted Unix partition {partition_identifier}')
                return {'success': True, 'message': 'Partition formatted successfully'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_partition_info(self, partition_identifier: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._get_windows_partition_info(partition_identifier)
            else:
                return self._get_unix_partition_info(partition_identifier)
        except Exception as e:
            return {'error': str(e)}
    
    def _get_windows_partition_info(self, partition_identifier: str) -> Dict:
        try:
            command = f'Get-Partition -PartitionNumber {partition_identifier} | ConvertTo-Json'
            
            result = subprocess.run([
                'powershell', '-Command', command
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'number': data.get('PartitionNumber', 0),
                    'letter': data.get('DriveLetter', ''),
                    'size': data.get('Size', 0),
                    'type': data.get('Type', ''),
                    'disk': data.get('DiskNumber', 0)
                }
            else:
                return {'error': result.stderr}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_unix_partition_info(self, partition_identifier: str) -> Dict:
        try:
            command = f'lsblk -f -J {partition_identifier}'
            
            result = subprocess.run(command.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                device = data.get('blockdevices', [{}])[0]
                
                return {
                    'name': device.get('name', ''),
                    'fstype': device.get('fstype', ''),
                    'size': device.get('size', ''),
                    'mountpoint': device.get('mountpoint', ''),
                    'label': device.get('label', ''),
                    'uuid': device.get('uuid', '')
                }
            else:
                return {'error': result.stderr}
                
        except Exception as e:
            return {'error': str(e)}
    
    def get_operation_log(self) -> List[str]:
        return self.operation_log.copy()
    
    def clear_operation_log(self):
        self.operation_log.clear()

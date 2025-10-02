import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional

class BootloaderManager:
    def __init__(self):
        self.bootloader_configs = {}
        self.grub_config_path = "/etc/grub.d"
        self.windows_boot_path = "C:\\Windows\\Boot"
        
    def configure_bootloader(self, target_partition: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._configure_windows_bootloader(target_partition)
            else:
                return self._configure_grub_bootloader(target_partition)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _configure_windows_bootloader(self, target_partition: str) -> Dict:
        try:
            bcd_commands = [
                f'bcdedit /create /d "Detorrent OS" /application bootsector',
                f'bcdedit /set {{bootmgr}} timeout 10',
                f'bcdedit /set {{bootmgr}} displayorder {{default}}'
            ]
            
            for command in bcd_commands:
                result = subprocess.run([
                    'powershell', '-Command', command
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'BCD command failed: {result.stderr}'}
            
            return {'success': True, 'message': 'Windows bootloader configured'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _configure_grub_bootloader(self, target_partition: str) -> Dict:
        try:
            grub_config = self._generate_grub_config(target_partition)
            config_path = "/etc/grub.d/40_detorrent"
            
            with open(config_path, 'w') as f:
                f.write(grub_config)
            
            os.chmod(config_path, 0o755)
            
            result = subprocess.run([
                'sudo', 'update-grub'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'GRUB bootloader configured'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_grub_config(self, target_partition: str) -> str:
        return f"""#!/bin/sh
exec tail -n +3 $0

menuentry 'Detorrent OS' {{
    set root='hd0,{target_partition}'
    linux /boot/vmlinuz root={target_partition} ro quiet splash
    initrd /boot/initrd.img
}}
"""
    
    def list_boot_entries(self) -> List[Dict]:
        try:
            if os.name == 'nt':
                return self._list_windows_boot_entries()
            else:
                return self._list_grub_boot_entries()
        except Exception as e:
            return [{'error': str(e)}]
    
    def _list_windows_boot_entries(self) -> List[Dict]:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'bcdedit /enum | Select-String "description"'
            ], capture_output=True, text=True)
            
            entries = []
            for line in result.stdout.split('\n'):
                if 'description' in line.lower():
                    entries.append({'description': line.strip()})
            
            return entries
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def _list_grub_boot_entries(self) -> List[Dict]:
        try:
            grub_config_path = "/etc/default/grub"
            if not os.path.exists(grub_config_path):
                return []
            
            with open(grub_config_path, 'r') as f:
                content = f.read()
            
            entries = []
            lines = content.split('\n')
            for line in lines:
                if line.startswith('GRUB_DEFAULT'):
                    entries.append({'default': line.split('=')[1].strip('"')})
            
            return entries
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def set_default_boot_entry(self, entry_name: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._set_windows_default_entry(entry_name)
            else:
                return self._set_grub_default_entry(entry_name)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _set_windows_default_entry(self, entry_name: str) -> Dict:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                f'bcdedit /set {{bootmgr}} default {entry_name}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Default boot entry set'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _set_grub_default_entry(self, entry_name: str) -> Dict:
        try:
            grub_config_path = "/etc/default/grub"
            
            with open(grub_config_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('GRUB_DEFAULT'):
                    lines[i] = f'GRUB_DEFAULT="{entry_name}"'
                    break
            
            with open(grub_config_path, 'w') as f:
                f.write('\n'.join(lines))
            
            result = subprocess.run([
                'sudo', 'update-grub'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Default boot entry set'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def remove_boot_entry(self, entry_name: str) -> Dict:
        try:
            if os.name == 'nt':
                return self._remove_windows_boot_entry(entry_name)
            else:
                return self._remove_grub_boot_entry(entry_name)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _remove_windows_boot_entry(self, entry_name: str) -> Dict:
        try:
            result = subprocess.run([
                'powershell', '-Command',
                f'bcdedit /delete {entry_name}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Boot entry removed'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _remove_grub_boot_entry(self, entry_name: str) -> Dict:
        try:
            config_path = f"/etc/grub.d/40_{entry_name}"
            if os.path.exists(config_path):
                os.remove(config_path)
            
            result = subprocess.run([
                'sudo', 'update-grub'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': 'Boot entry removed'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

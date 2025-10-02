import os
import subprocess
import platform
import psutil
from typing import Dict, List, Optional
import json
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.monitoring_active = False
        self.system_metrics = {}
        
    def get_comprehensive_info(self) -> Dict:
        try:
            system_info = {
                'platform': self._get_platform_info(),
                'hardware': self._get_hardware_info(),
                'memory': self._get_memory_info(),
                'storage': self._get_storage_info(),
                'network': self._get_network_info(),
                'processes': self._get_process_info(),
                'boot': self._get_boot_info(),
                'timestamp': datetime.now().isoformat()
            }
            
            return system_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_platform_info(self) -> Dict:
        try:
            return {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0],
                'hostname': platform.node(),
                'python_version': platform.python_version()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_hardware_info(self) -> Dict:
        try:
            cpu_info = {
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'frequency': psutil.cpu_freq(),
                'usage_percent': psutil.cpu_percent(interval=1)
            }
            
            return {
                'cpu': cpu_info,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'uptime': datetime.now().timestamp() - psutil.boot_time()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_memory_info(self) -> Dict:
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_storage_info(self) -> List[Dict]:
        try:
            storage_info = []
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    storage_info.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100
                    })
                except PermissionError:
                    continue
            
            return storage_info
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_network_info(self) -> Dict:
        try:
            network_info = {
                'interfaces': [],
                'connections': []
            }
            
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'name': interface,
                    'addresses': []
                }
                
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                
                network_info['interfaces'].append(interface_info)
            
            for conn in psutil.net_connections(kind='inet'):
                network_info['connections'].append({
                    'fd': conn.fd,
                    'family': str(conn.family),
                    'type': str(conn.type),
                    'laddr': conn.laddr,
                    'raddr': conn.raddr,
                    'status': conn.status,
                    'pid': conn.pid
                })
            
            return network_info
        except Exception as e:
            return {'error': str(e)}
    
    def _get_process_info(self) -> List[Dict]:
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:20]
        except Exception as e:
            return [{'error': str(e)}]
    
    def _get_boot_info(self) -> Dict:
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
                'Get-WmiObject -Class Win32_ComputerSystem | Select-Object BootupState, SystemStartupOptions'
            ], capture_output=True, text=True)
            
            boot_info = {
                'bootloader': 'Windows Boot Manager',
                'boot_state': 'Unknown',
                'startup_options': []
            }
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'BootupState' in line:
                        boot_info['boot_state'] = line.split(':')[1].strip()
            
            return boot_info
        except Exception as e:
            return {'error': str(e)}
    
    def _get_unix_boot_info(self) -> Dict:
        try:
            boot_info = {
                'bootloader': 'GRUB',
                'config_path': '/etc/default/grub'
            }
            
            if os.path.exists('/etc/default/grub'):
                with open('/etc/default/grub', 'r') as f:
                    content = f.read()
                
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('GRUB_DEFAULT'):
                        boot_info['default_entry'] = line.split('=')[1].strip('"')
                    elif line.startswith('GRUB_TIMEOUT'):
                        boot_info['timeout'] = line.split('=')[1].strip('"')
            
            return boot_info
        except Exception as e:
            return {'error': str(e)}
    
    def start_monitoring(self, interval: int = 5) -> Dict:
        try:
            self.monitoring_active = True
            self.system_metrics = {}
            
            return {'success': True, 'message': f'Monitoring started with {interval}s interval'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_monitoring(self) -> Dict:
        try:
            self.monitoring_active = False
            return {'success': True, 'message': 'Monitoring stopped'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_current_metrics(self) -> Dict:
        try:
            if not self.monitoring_active:
                return {'error': 'Monitoring not active'}
            
            current_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': {},
                'network_io': psutil.net_io_counters()._asdict(),
                'timestamp': datetime.now().isoformat()
            }
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    current_metrics['disk_usage'][partition.mountpoint] = {
                        'percent': (usage.used / usage.total) * 100,
                        'free_gb': usage.free / (1024**3)
                    }
                except PermissionError:
                    continue
            
            return current_metrics
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_health(self) -> Dict:
        try:
            health_status = {
                'overall': 'good',
                'issues': [],
                'recommendations': []
            }
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80:
                health_status['issues'].append('High CPU usage')
                health_status['recommendations'].append('Close unnecessary applications')
            
            if memory_percent > 85:
                health_status['issues'].append('High memory usage')
                health_status['recommendations'].append('Free up memory or add more RAM')
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_percent = (usage.used / usage.total) * 100
                    
                    if disk_percent > 90:
                        health_status['issues'].append(f'Low disk space on {partition.mountpoint}')
                        health_status['recommendations'].append(f'Free up space on {partition.mountpoint}')
                except PermissionError:
                    continue
            
            if health_status['issues']:
                health_status['overall'] = 'warning'
            
            return health_status
        except Exception as e:
            return {'error': str(e)}
    
    def get_process_by_name(self, process_name: str) -> List[Dict]:
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent'],
                            'status': proc.info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return processes
        except Exception as e:
            return [{'error': str(e)}]
    
    def kill_process(self, pid: int) -> Dict:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            return {'success': True, 'message': f'Process {pid} terminated'}
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                return {'success': True, 'message': f'Process {pid} killed'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

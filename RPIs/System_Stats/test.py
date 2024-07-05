from flask import Flask, jsonify
import psutil
import platform
from datetime import datetime

app = Flask(__name__)

def get_system_stats():
    # Uptime
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    uptime = (datetime.now() - bt).total_seconds()

    # CPU stats
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_freq = psutil.cpu_freq()
    cpu_stats = psutil.cpu_stats()

    # Memory stats
    memory_info = psutil.virtual_memory()
    swap_info = psutil.swap_memory()

    # Disk stats
    disk_info = psutil.disk_usage('/')
    disk_partitions = psutil.disk_partitions()

    # Network stats
    net_io_counters = psutil.net_io_counters(pernic=True)

    # System info
    uname = platform.uname()
    
    stats = {
        'uptime_seconds': uptime,
        'cpu': {
            'percent_per_core': cpu_percent,
            'frequency': {
                'current': cpu_freq.current,
                'min': cpu_freq.min,
                'max': cpu_freq.max
            },
            'stats': {
                'ctx_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
                'soft_interrupts': cpu_stats.soft_interrupts,
                'syscalls': cpu_stats.syscalls
            }
        },
        'memory': {
            'total': memory_info.total,
            'available': memory_info.available,
            'percent': memory_info.percent,
            'used': memory_info.used,
            'free': memory_info.free,
            'active': memory_info.active,
            'inactive': memory_info.inactive,
            'buffers': memory_info.buffers,
            'cached': memory_info.cached,
            'shared': memory_info.shared,
            'swap': {
                'total': swap_info.total,
                'used': swap_info.used,
                'free': swap_info.free,
                'percent': swap_info.percent,
                'sin': swap_info.sin,
                'sout': swap_info.sout
            }
        },
        'disk': {
            'total': disk_info.total,
            'used': disk_info.used,
            'free': disk_info.free,
            'percent': disk_info.percent,
            'partitions': [
                {
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts
                } for partition in disk_partitions
            ]
        },
        'network': {
            interface: {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout
            } for interface, stats in net_io_counters.items()
        },
        'system': {
            'system': uname.system,
            'node_name': uname.node,
            'release': uname.release,
            'version': uname.version,
            'machine': uname.machine,
            'processor': uname.processor
        }
    }

    return stats

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify(get_system_stats())

if __name__ == '__main__':
    app.run(host='robotpi.local', port=5000)

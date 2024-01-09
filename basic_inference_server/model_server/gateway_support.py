import psutil
import sys
import platform

from .request_utils import MSCT

MONITORED_PACKAGES = [
  'numpy',
  'flask',
  'transformers',
  'torch',
  'tensorflow',
  'accelerate',
  'tokenizers',
  'Werkzeug',
  'python-telegram-bot',  
]


def get_packages(monitored_packages=None):
  import pkg_resources
  packs = [x for x in pkg_resources.working_set]
  maxlen = max([len(x.key) for x in packs]) + 1
  if isinstance(monitored_packages, list) and len(monitored_packages) > 0:
    packs = [
      "{}{}".format(x.key + ' ' * (maxlen - len(x.key)), x.version) for x in packs    
      if x.key in monitored_packages
    ]
  else:
    packs = [
      "{}{}".format(x.key + ' ' * (maxlen - len(x.key)), x.version) for x in packs    
    ]
  packs = sorted(packs)  
  return packs  


class _GatewaySupportMixin(object):
  def __init__(self) -> None:
    super(_GatewaySupportMixin, self).__init__()
    self.__support_status = {}
    return

  def _get_system_status(self, display=True):
    mem_total = round(self.log.get_machine_memory(gb=True),2)
    mem_avail = round(self.log.get_avail_memory(gb=True),2)
    mem_gateway = round(self.log.get_current_process_memory(mb=False),2)
    disk_total = round(self.log.get_total_disk(),2)
    disk_avail = round(self.log.get_avail_disk(),2)
    
    mem_servers = 0
    dct_servers = {
    }
    for svr in self._servers:
      proc = psutil.Process(self._servers[svr][MSCT.PROCESS].pid)
      proc_mem = round(proc.memory_info().rss / (1024**3), 2)
      mem_servers += proc_mem
      dct_servers[svr] = proc_mem
    #endfor calc mem
    mem_used = round(mem_gateway + mem_servers, 2)
    mem_sys = round((mem_total - mem_avail) - mem_used,2)
    server_name = self.config_data.get(MSCT.SERVER_NAME, 'base_ai_app')
    self.P("Information for server '{}':".format(server_name))
    self.P("  Total server memory:    {:>5.1f} GB".format(mem_total), color='g')
    self.P("  Total server avail mem: {:>5.1f} GB".format(mem_avail), color='g')
    self.P("  Total allocated mem:    {:>5.1f} GB".format(mem_used), color='g')
    self.P("  System allocated mem:   {:>5.1f} GB".format(mem_sys), color='g')
    self.P("  Disk free:   {:>5.1f} GB".format(disk_avail), color='g')
    self.P("  Disk total:  {:>5.1f} GB".format(disk_total), color='g')
    
    mem_alert = (mem_avail / mem_total) < MSCT.MEM_ALERT_THR
    disk_alert = (disk_avail / disk_total) < MSCT.DISK_ALERT_THR
    
    alerts = []
    if mem_alert:
      alerts.append("Memory below {} threshold.".format(MSCT.MEM_ALERT_THR))
    if disk_alert:
      alerts.append("Disk below {} threshold.".format(MSCT.DISK_ALERT_THR))
    dct_system_alert = dict(
      mem_alert=mem_alert,
      disk_alert=disk_alert,
      alerts=alerts,
    )
    
    dct_stats = dict(
      server_name=server_name,
      mem_total=mem_total,
      mem_avail=mem_avail,
      mem_gateway=mem_gateway,
      mem_used=mem_used,
      mem_sys=mem_sys,
      mem_servers=dct_servers,
      disk_avail=disk_avail,
      disk_total=disk_total,    
      system=platform.platform(),
      py=sys.version,
      monitored_packages=get_packages(monitored_packages=MONITORED_PACKAGES),
      info='Memory Size is in GB. Total and avail mem may be reported inconsistently in containers.',
      system_support_services=self.__support_status,
    )
    return dct_stats, dct_system_alert  
  
  def _process_support_data(self, signature, data):
    """
    Process the data received from the support process.
    """
    self.__support_status[signature] = data
    return
  
  
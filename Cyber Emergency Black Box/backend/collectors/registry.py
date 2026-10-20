import json
from pathlib import Path
from backend.collectors.system_info_collector import SystemInfoCollector
from backend.collectors.process_collector import ProcessCollector
from backend.collectors.network_collector import NetworkCollector
from backend.collectors.file_collector import FileCollector
from backend.collectors.login_collector import LoginCollector
from backend.collectors.usb_collector import USBCollector
def get_enabled_collectors(ingest, enabled_names, paths=()):
    names=set(json.loads(enabled_names) if isinstance(enabled_names,str) and enabled_names.startswith("[") else str(enabled_names).split(","))
    choices={"system_info":SystemInfoCollector(ingest),"process":ProcessCollector(ingest),"network":NetworkCollector(ingest),"file":FileCollector(ingest,paths),"login":LoginCollector(ingest),"usb":USBCollector(ingest)}
    return [collector for name,collector in choices.items() if name in names]

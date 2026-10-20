import asyncio, json, logging, time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config import settings, ensure_directories
from backend.database.engine import init_db,get_db,get_session_factory
from backend.database import crud
from backend.database.retention import purge_old_events
from backend.models.event import EventCreate,event_dict
from backend.models.incident import IncidentStatusUpdate,incident_dict
from backend.collectors.normaliser import normalise
from backend.collectors.registry import get_enabled_collectors
from backend.collectors.system_info_collector import SystemInfoCollector
from backend.correlation.engine import CorrelationEngine
from backend.evidence.manager import EvidenceManager
from backend.reports.html_report import generate_html_report
from simulator.scenarios.account_compromise import AccountCompromiseScenario

logging.basicConfig(level=getattr(logging,settings.log_level)); started=time.monotonic()
def ok(data,meta=None): return {"data":data,"meta":meta or {}}
async def ingest(raw):
    event=normalise(raw)
    async with get_session_factory()() as session:
        saved=await crud.insert_event(session,event); await CorrelationEngine().run_once(session); return saved
async def _maintenance():
    while True:
        try:
            for collector in getattr(app.state,"collectors",[]):
                await collector.run_once()
            async with get_session_factory()() as session:
                await CorrelationEngine().run_once(session); await purge_old_events(session,settings.retention_minutes)
        except Exception: logging.exception("maintenance cycle failed")
        await asyncio.sleep(settings.correlation_interval_seconds)
@asynccontextmanager
async def lifespan(app):
    ensure_directories(); await init_db(); app.state.collectors=get_enabled_collectors(ingest,settings.enabled_collectors,settings.monitored_paths.split(","))
    async with get_session_factory()() as session:
        snapshot=await SystemInfoCollector(ingest).snapshot()
        await crud.insert_system_snapshot(session,snapshot)
    for c in app.state.collectors:
        if hasattr(c,"start"): c.start()
    app.state.maintenance=asyncio.create_task(_maintenance())
    yield
    app.state.maintenance.cancel()
    for c in app.state.collectors:
        if hasattr(c,"stop"): c.stop()
app=FastAPI(title="Cyber Emergency Black Box",version="1.0",lifespan=lifespan)

@app.exception_handler(Exception)
async def safe_error(request, exc):
    logging.exception("Unhandled request failure"); return __import__('fastapi').responses.JSONResponse(status_code=500,content={"error":{"code":"internal_error","message":"An internal error occurred."}})

@app.get("/api/v1/health")
async def health(): return ok({"status":"ok"})
@app.post("/api/v1/events")
async def create_event(body:EventCreate): return ok(event_dict(await ingest(body.model_dump())))
@app.get("/api/v1/events")
async def events(limit:int=Query(100,le=500),offset:int=0,event_type:str|None=None,severity:str|None=None,simulated_only:bool|None=None,db:AsyncSession=Depends(get_db)):
    rows=await crud.get_events(db,limit,offset,event_type,severity,None,simulated_only); return ok([event_dict(x) for x in rows],{"limit":limit,"offset":offset,"count":len(rows)})
@app.get("/api/v1/events/stats")
async def event_stats(db:AsyncSession=Depends(get_db)):
    rows=await crud.get_events(db,5000); out={}
    for row in rows: out[row.event_type]=out.get(row.event_type,0)+1
    return ok(out)
@app.get("/api/v1/events/{event_id}")
async def event(event_id:str,db:AsyncSession=Depends(get_db)):
    row=await crud.get_event_by_id(db,event_id)
    if not row: raise HTTPException(404,"event not found")
    return ok(event_dict(row))
@app.get("/api/v1/incidents")
async def incidents(status:str|None=None,severity:str|None=None,limit:int=100,offset:int=0,db:AsyncSession=Depends(get_db)):
    rows=await crud.get_incidents(db,status,severity,limit,offset); return ok([incident_dict(x) for x in rows])
@app.get("/api/v1/incidents/{incident_id}")
async def incident(incident_id:str,db:AsyncSession=Depends(get_db)):
    row=await crud.get_incident_by_id(db,incident_id)
    if not row: raise HTTPException(404,"incident not found")
    data=incident_dict(row); data["events"]=[event_dict(x) for x in await crud.get_events_for_incident(db,incident_id)]; return ok(data)
@app.patch("/api/v1/incidents/{incident_id}")
async def change_incident(incident_id:str,body:IncidentStatusUpdate,db:AsyncSession=Depends(get_db)):
    row=await crud.update_incident_status(db,incident_id,body.status)
    if not row: raise HTTPException(404,"incident not found")
    return ok(incident_dict(row))
@app.get("/api/v1/incidents/{incident_id}/timeline")
async def timeline(incident_id:str,db:AsyncSession=Depends(get_db)): return ok([event_dict(x) for x in await crud.get_events_for_incident(db,incident_id)])
@app.get("/api/v1/incidents/{incident_id}/evidence")
async def evidence(incident_id:str):
    try: return ok(EvidenceManager().get_manifest(incident_id))
    except FileNotFoundError: raise HTTPException(404,"evidence not found")
@app.get("/api/v1/incidents/{incident_id}/evidence/verify")
async def verify(incident_id:str): return ok(EvidenceManager().verify(incident_id))
@app.get("/api/v1/incidents/{incident_id}/evidence/download")
async def download(incident_id:str): return FileResponse(EvidenceManager().zip(incident_id),media_type="application/zip",filename=f"{incident_id}.zip")
@app.get("/api/v1/incidents/{incident_id}/report",response_class=HTMLResponse)
async def report(incident_id:str,db:AsyncSession=Depends(get_db)):
    item=await crud.get_incident_by_id(db,incident_id)
    if not item: raise HTTPException(404,"incident not found")
    return generate_html_report(item,await crud.get_events_for_incident(db,incident_id),item.interpretation or "",EvidenceManager().get_manifest(incident_id))
@app.post("/api/v1/simulator/run")
async def simulate():
    asyncio.create_task(AccountCompromiseScenario().run(ingest)); return ok({"started":True,"scenario":"account_compromise"})
@app.get("/api/v1/simulator/scenarios")
async def scenarios(): return ok(["account_compromise"])
@app.get("/api/v1/settings")
async def get_settings(db:AsyncSession=Depends(get_db)): return ok(await crud.get_settings(db))
@app.put("/api/v1/settings")
async def put_settings(body:dict,db:AsyncSession=Depends(get_db)):
    permitted={"retention_minutes","correlation_interval_seconds","evidence_context_minutes","enabled_collectors"}
    if not body or set(body)-permitted: raise HTTPException(422,"unsupported setting")
    for key in ("retention_minutes","correlation_interval_seconds","evidence_context_minutes"):
        if key in body and (not isinstance(body[key],int) or body[key] <= 0): raise HTTPException(422,f"{key} must be a positive integer")
    if "enabled_collectors" in body and (not isinstance(body["enabled_collectors"],list) or not set(body["enabled_collectors"]) <= {"login","process","file","network","system_info","usb"}): raise HTTPException(422,"invalid enabled collectors")
    return ok(await crud.update_settings(db,body))
@app.get("/api/v1/system/info")
async def system_info(db:AsyncSession=Depends(get_db)):
    snap=await crud.get_latest_system_snapshot(db)
    if not snap:
        snapshot=await SystemInfoCollector(ingest).snapshot(); snap=await crud.insert_system_snapshot(db,snapshot)
    return ok({"hostname":snap.hostname,"os_name":snap.os_name,"os_version":snap.os_version,"cpu_count":snap.cpu_count,"memory_total_gb":snap.memory_total_gb})
@app.get("/api/v1/system/status")
async def system_status(): return ok({"uptime_seconds":int(time.monotonic()-started),"collectors":[{"name":x.name,"available":x.available} for x in getattr(app.state,"collectors",[])]})
@app.get("/api/v1/dashboard/summary")
async def summary(db:AsyncSession=Depends(get_db)):
    events=await crud.event_count(db); incidents=await crud.get_incidents(db); return ok({"event_count":events,"incident_count":len(incidents),"highest_severity":next((x.severity for x in incidents),"INFO"),"uptime_seconds":int(time.monotonic()-started)})

if settings.frontend_dir.exists(): app.mount("/",StaticFiles(directory=settings.frontend_dir,html=True),name="frontend")

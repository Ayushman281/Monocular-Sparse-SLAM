import {useEffect, useRef, useState} from 'react';
import Viewer from './Viewer';
import type {Camera, Reconstruction} from './types';

const initialCamera:Camera={mode:'approximate',horizontal_fov:65,fx:535,fy:535,cx:320,cy:240,cols:640,rows:480,k1:0,k2:0,p1:0,p2:0,k3:0};
const sleep=(ms:number,signal:AbortSignal)=>new Promise<void>((resolve,reject)=>{
  if(signal.aborted) return reject(new DOMException('Aborted','AbortError'));
  const abort=()=>{clearTimeout(timer);reject(new DOMException('Aborted','AbortError'));};
  const timer=window.setTimeout(()=>{signal.removeEventListener('abort',abort);resolve();},ms);
  signal.addEventListener('abort',abort,{once:true});
});
async function responseJSON(response:Response) {
  const data=await response.json();
  if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'The server could not handle this request.');
  return data;
}

export default function App() {
  const [config,setConfig]=useState({preview:true,apiBase:''});
  const [ready,setReady]=useState(false);
  const [limits,setLimits]=useState({max_video_size_mb:200,max_duration_seconds:30,job_ttl_seconds:1800});
  const [file,setFile]=useState<File|null>(null);
  const [url,setUrl]=useState('');
  const [duration,setDuration]=useState<number|null>(null);
  const [camera,setCamera]=useState<Camera>(initialCamera);
  const [result,setResult]=useState<Reconstruction|null>(null);
  const [stage,setStage]=useState('');
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [dragging,setDragging]=useState(false);
  const [uploadTime,setUploadTime]=useState<number|null>(null);
  const [pendingJob,setPendingJob]=useState<string|null>(null);
  const picker=useRef<HTMLInputElement>(null);
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>{
    const abort=new AbortController();
    (async()=>{
      const c=await fetch('/app-config.json',{signal:abort.signal,cache:'no-store'}).then(responseJSON);
      setConfig(c);
      if(c.preview) return;
      const [health,system]=await Promise.all([
        fetch(`${c.apiBase}/api/health`,{signal:abort.signal}).then(responseJSON),
        fetch(`${c.apiBase}/api/system`,{signal:abort.signal}).then(responseJSON)]);
      setLimits(system);setReady(health.slam_runner_available && health.slam_enabled);
      if(!health.slam_runner_available) setError('The server is available, but its SLAM engine is not ready.');
    })().catch(e=>{if(e.name!=='AbortError')setError('Could not connect to the server. Reload to try again.');});
    return()=>{abort.abort();controller.current?.abort();};
  },[]);
  useEffect(()=>{if(!file){setUrl('');return;}const next=URL.createObjectURL(file);setUrl(next);return()=>URL.revokeObjectURL(next);},[file]);
  function choose(next?:File) {
    if(!next || busy) return;
    if(next.size>limits.max_video_size_mb*1024**2){setError(`Choose a video smaller than ${limits.max_video_size_mb} MB.`);return;}
    setFile(next);setDuration(null);setResult(null);setError('');setStage('');setUploadTime(null);setPendingJob(null);
  }
  async function watch(jobId:string,signal:AbortSignal) {
    for(;;){
      await sleep(600,signal);
      const status=await fetch(`${config.apiBase}/api/v1/slam/${jobId}`,{signal}).then(responseJSON);
      setStage(status.stage);
      if(status.status==='success'){setResult(status.result);setPendingJob(null);break;}
      if(status.status==='failed'){setPendingJob(null);throw new Error(status.error || 'Reconstruction failed.');}
    }
  }
  async function run() {
    if(!file || !ready || busy) return;
    setBusy(true);setError('');setResult(null);setStage(pendingJob?'Checking reconstruction':'Uploading');
    const abort=new AbortController();controller.current=abort;
    try {
      let jobId=pendingJob;
      if(!jobId){
        const form=new FormData();form.append('video',file);form.append('camera',JSON.stringify(camera));
        const start=performance.now();
        const response=await fetch(`${config.apiBase}/api/v1/slam/process`,{method:'POST',body:form,signal:abort.signal}).then(responseJSON);
        setUploadTime((performance.now()-start)/1000);jobId=response.job_id as string;setPendingJob(jobId);
      }
      await watch(jobId,abort.signal);
    } catch(e){if(e instanceof Error && e.name!=='AbortError')setError(e.message);}
    finally {setBusy(false);}
  }
  const numberField=(name:keyof Omit<Camera,'mode'>,label:string)=> <label key={name}>{label}<input type="number" step="any" value={camera[name]} onChange={e=>setCamera({...camera,[name]:e.target.valueAsNumber})}/></label>;
  return <div className="app-shell">
    <header><a className="brand" href="/" aria-label="O-Hive Atlas home"><span className="brand-mark">⌘</span><strong>O-HIVE<span> / ATLAS</span></strong></a><div className="header-meta"><span>MONOCULAR SLAM LAB</span><span className={`connection ${ready?'online':''}`}><i/>{config.preview?'Interface preview':ready?'Engine ready':'Connecting'}</span></div></header>
    <main><div className="intro"><div className="eyebrow"><span className="mint-text">02</span> / SPATIAL RECONSTRUCTION</div><h1>Monocular RGB<br/><span>Sparse Point Cloud SLAM</span></h1><p>Estimate camera motion and reconstruct a sparse 3D map<br className="desktop-break"/> from a single RGB video.</p><div className="engine-tag">stella_vslam 0.7.0 <span>·</span> CPU processing <span>·</span> Single camera</div></div>
    <div className="workspace"><aside><section className="upload-panel"><div className="panel-heading"><div><span className="eyebrow">01 / INPUT</span><h2>Start with a video</h2></div><span className="small-tag">RGB</span></div>
      <div className={`dropzone ${dragging?'dragging':''}`} onDragOver={e=>{e.preventDefault();setDragging(true);}} onDragLeave={()=>setDragging(false)} onDrop={e=>{e.preventDefault();setDragging(false);choose(e.dataTransfer.files[0]);}}>
        {file?<><video src={url} controls preload="metadata" onLoadedMetadata={e=>setDuration(e.currentTarget.duration)} onError={()=>setDuration(null)}/><div className="file-row"><div><strong>{file.name}</strong><span>{(file.size/1024**2).toFixed(1)} MB{duration && Number.isFinite(duration)?` · ${duration.toFixed(1)} seconds`:''}</span></div><button className="quiet" disabled={busy} onClick={()=>picker.current?.click()}>Change</button></div></>:<><div className="upload-icon">↥</div><h3>Drop your video here</h3><p>A short walk. A room. A new viewpoint.</p><button className="browse" disabled={busy} onClick={()=>picker.current?.click()}>Browse files <span>↗</span></button><small>MP4, MOV, WebM, AVI · Up to {limits.max_video_size_mb} MB</small></>}
        <input ref={picker} className="sr-only" type="file" accept=".mp4,.mov,.webm,.avi,video/*" onChange={e=>{choose(e.target.files?.[0]);e.target.value='';}} aria-label="Choose video" disabled={busy}/>
      </div>
      <details className="camera-settings"><summary>Advanced camera settings <span>Optional</span></summary><fieldset disabled={busy}><label>Camera mode<select value={camera.mode} onChange={e=>setCamera({...camera,mode:e.target.value as Camera['mode']})}><option value="approximate">Approximate from field of view</option><option value="calibrated">Calibrated camera intrinsics</option></select></label>{camera.mode==='approximate'?<>{numberField('horizontal_fov','Horizontal field of view (°)')}<p>Estimated intrinsics may reduce trajectory and map accuracy.</p></>:<><p>Enter calibration for the video’s upright, original resolution.</p><div className="intrinsics">{(['fx','fy','cx','cy','cols','rows','k1','k2','p1','p2','k3'] as const).map(k=>numberField(k,k))}</div></>}</fieldset></details>
      <button className="run-button" onClick={run} disabled={!file||!ready||busy}>{busy?<><span className="spinner"/>{stage}</>:pendingJob?'Check existing reconstruction':<>Run reconstruction <span>→</span></>}</button>
      <div role="status" aria-live="polite">{config.preview && <p className="preview-note">Interface preview · Processing becomes available on the hosted server.</p>}{stage&&!busy&&!error&&<p className="success-note">{stage}</p>}</div>
      {error&&<div className="error" role="alert">{error}</div>}
    </section><section className="capture-guide"><span className="eyebrow">A BETTER CAPTURE</span><h3>Move through the scene.</h3><p>Use a textured, well-lit space. Move slowly with some sideways motion. Return toward your starting view to give loop detection a chance.</p><div><span>↔ Translation</span><span>◐ Good lighting</span><span>⤺ Revisit</span></div></section></aside>
    <div className="output-column"><Viewer result={result}/><section className="metrics-panel"><div className="metrics-title"><span className="eyebrow">02 / PERFORMANCE</span><span>{result?'Measured server results':'Waiting for a reconstruction'}</span></div><div className="metrics">{[
      ['Server processing',result?`${result.processing.processing_time_seconds.toFixed(2)} s`:'—'],
      ['Real-time factor',result?`${result.processing.real_time_factor.toFixed(2)}×`:'—'],
      ['Camera keyframes',result?result.slam.keyframes.toLocaleString():'—'],
      ['Sparse landmarks',result?result.slam.map_points.toLocaleString():'—']
    ].map(([label,value])=><div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
      {result&&<><div className="result-details"><span>Native process: {result.processing.slam_process_seconds.toFixed(2)} s</span><span>Tracked: {result.slam.frames_tracked}/{result.slam.frames_processed} frames</span><span>Loop edges: {result.slam.loop_edges}</span><span>Upload + acceptance: {uploadTime?.toFixed(2)} s</span><span>{result.video.processing_width} × {result.video.processing_height} at {result.video.processed_fps.toFixed(1)} FPS</span></div><div className="downloads">{['trajectory.csv','pointcloud.ply','result.json'].map(name=><a key={name} href={`${config.apiBase}/api/v1/slam/${result.job_id}/${name}`} download>↓ {name}</a>)}</div></>}
    </section><div className="scale-note"><span>ⓘ</span><p><strong>Relative / arbitrary scale.</strong> Monocular RGB cannot determine absolute metric scale from vision alone. Coordinates are not metres.</p></div>{result?.warnings.filter(w=>!w.includes('arbitrary global scale')).map(w=><div className="scale-note" key={w}>{w}</div>)}</div></div>
    <footer><span>ORB features → camera tracking → optimized sparse map</span><span>Temporary processing · Results expire after {Math.round(limits.job_ttl_seconds/60)} minutes</span></footer>
    </main></div>;
}

import {useEffect, useRef, useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import type {Reconstruction} from './types';

export default function Viewer({result}: {result: Reconstruction|null}) {
  const host = useRef<HTMLDivElement>(null);
  const reset = useRef<() => void>(() => {});
  const [error, setError] = useState('');
  const [showPoints, setShowPoints] = useState(true);
  const [showPath, setShowPath] = useState(true);
  useEffect(() => {
    if (!host.current) return;
    const container = host.current;
    let renderer: THREE.WebGLRenderer;
    try { renderer = new THREE.WebGLRenderer({antialias: true, alpha: true}); }
    catch { setError('WebGL is unavailable. Download the PLY and trajectory to view them in a 3D application.'); return; }
    setError('');
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);
    renderer.domElement.setAttribute('aria-label', '3D reconstruction: drag to rotate, scroll to zoom, right-drag to pan');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, .001, 100000);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    // One rigid display transform for BOTH landmarks and poses: (x,-y,-z).
    const position = (p: number[]) => new THREE.Vector3(p[0], -p[1], -p[2]);
    const xyz = result?.points.map(position) ?? [];
    const path = result?.trajectory.map(p => position(p.slice(1,4))) ?? [];
    const bounds = new THREE.Box3();
    for (const p of [...xyz, ...path]) bounds.expandByPoint(p);
    const center = bounds.isEmpty() ? new THREE.Vector3() : bounds.getCenter(new THREE.Vector3());
    const size = bounds.isEmpty() ? 8 : Math.max(bounds.getSize(new THREE.Vector3()).length(), .01);
    const grid = new THREE.GridHelper(size * 2, 24, 0x30444c, 0x1b2b33);
    grid.position.copy(center); grid.position.y -= size * .25; scene.add(grid);
    if (showPoints && xyz.length) {
      scene.add(new THREE.Points(new THREE.BufferGeometry().setFromPoints(xyz),
        new THREE.PointsMaterial({color:0x6be7c2, size:2, sizeAttenuation:false, transparent:true, opacity:.8})));
    }
    if (showPath && path.length) {
      // Do not draw a continuous trajectory across untracked time gaps.
      const segments: THREE.Vector3[] = [];
      const gap = 1.6 / (result?.video.processed_fps ?? 15);
      for (let i=1; i<path.length; i++) {
        if (result!.trajectory[i][0] - result!.trajectory[i-1][0] <= gap) segments.push(path[i-1], path[i]);
      }
      scene.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(segments), new THREE.LineBasicMaterial({color:0xada4ff})));
      [path[0],path[path.length-1]].forEach((p,i) => {
        const marker = new THREE.Mesh(new THREE.SphereGeometry(size*.009,16,12), new THREE.MeshBasicMaterial({color:i ? 0xffc273 : 0x6be7c2}));
        marker.position.copy(p); scene.add(marker);
      });
    }
    const axes = new THREE.AxesHelper(size * .12); axes.position.copy(center); scene.add(axes);
    reset.current = () => {
      camera.near = size / 10000; camera.far = size * 100;
      camera.position.copy(center).add(new THREE.Vector3(size*.65, size*.45, size*.75));
      controls.target.copy(center); camera.updateProjectionMatrix(); controls.update();
    };
    reset.current();
    const resize = new ResizeObserver(() => {
      const w=container.clientWidth, h=container.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix();
    });
    resize.observe(container);
    let animation=0;
    const draw=()=>{ animation=requestAnimationFrame(draw); controls.update(); renderer.render(scene,camera); };
    draw();
    return () => {
      cancelAnimationFrame(animation); resize.disconnect(); controls.dispose();
      scene.traverse(obj => {
        if ('geometry' in obj) (obj as THREE.Mesh).geometry.dispose();
        if ('material' in obj) {
          const material=(obj as THREE.Mesh).material;
          (Array.isArray(material)?material:[material]).forEach(m=>m.dispose());
        }
      });
      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove();
    };
  }, [result, showPoints, showPath]);
  return <section className="viewer-panel">
    <div className="panel-heading"><div><span className="eyebrow">RECONSTRUCTION</span><h2>Your space, in 3D</h2></div><button className="quiet" onClick={()=>reset.current()}>Reset view ↗</button></div>
    <div className="viewport"><div ref={host} className="canvas"/>{(!result || error) && <div className="empty"><div className="empty-icon">⌖</div><h3>{error?'Viewer unavailable':'A new perspective awaits'}</h3><p>{error || 'Upload a video to reconstruct its camera path and sparse 3D landmarks.'}</p></div>}<div className="viewport-label">PERSPECTIVE <span>·</span> RELATIVE SCALE</div></div>
    <div className="viewer-toolbar"><div className="legend"><label><input type="checkbox" checked={showPoints} onChange={e=>setShowPoints(e.target.checked)}/><i className="dot mint"/>Landmarks</label><label><input type="checkbox" checked={showPath} onChange={e=>setShowPath(e.target.checked)}/><i className="dot lavender"/>Trajectory</label>{result && <span><i className="dot amber"/>End</span>}</div><span className="gesture-help">Drag to orbit · Scroll to zoom · Right-drag to pan</span></div>
  </section>;
}

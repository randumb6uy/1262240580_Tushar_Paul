import { useEffect, useRef } from "react";
import type { StudioPlan } from "@/lib/concierge";

export function RoomScene({ plan }: { plan: StudioPlan }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let disposed=false, frame=0, cleanup=()=>{};
    import("three").then(async (THREE) => {
      if(disposed || !host.current) return;
      const { OrbitControls } = await import("three/examples/jsm/controls/OrbitControls.js");
      if(disposed || !host.current) return;
      const el=host.current, scene=new THREE.Scene(); scene.background=new THREE.Color(0xf4f2ed);
      const camera=new THREE.PerspectiveCamera(42,1,.1,100); camera.position.set(7,6,8);
      const renderer=new THREE.WebGLRenderer({antialias:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); el.appendChild(renderer.domElement);
      const material=new THREE.MeshLambertMaterial({color:0xd8d4cc});
      const floor=new THREE.Mesh(new THREE.BoxGeometry(plan.length,.12,plan.width),new THREE.MeshLambertMaterial({color:0xe9e6df})); scene.add(floor);
      const wallMat=new THREE.MeshLambertMaterial({color:0xf8f7f3});
      const back=new THREE.Mesh(new THREE.BoxGeometry(plan.length,3,.12),wallMat); back.position.set(0,1.5,-plan.width/2); scene.add(back);
      const side=new THREE.Mesh(new THREE.BoxGeometry(.12,3,plan.width),wallMat); side.position.set(-plan.length/2,1.5,0); scene.add(side);
      plan.products.forEach((p,i)=>{ const d=p.dimensions; const mesh=new THREE.Mesh(new THREE.BoxGeometry(Math.min(d.width,2.4),Math.min(d.height,1.5),Math.min(d.depth,2)), i===0?new THREE.MeshLambertMaterial({color:0x5b7290}):material); mesh.position.set(-plan.length/2+1.2+(i%3)*2.25,Math.min(d.height,1.5)/2+.08,-plan.width/2+1+(Math.floor(i/3))*2); scene.add(mesh); });
      scene.add(new THREE.HemisphereLight(0xffffff,0x777777,2.4)); const key=new THREE.DirectionalLight(0xffffff,2); key.position.set(4,8,6); scene.add(key);
      const controls=new OrbitControls(camera,renderer.domElement); controls.target.set(0,1,0); controls.enableDamping=true; controls.maxPolarAngle=Math.PI/2.05;
      const resize=()=>{ const w=el.clientWidth,h=el.clientHeight; renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix(); }; resize(); const observer=new ResizeObserver(resize); observer.observe(el);
      const tick=()=>{ controls.update(); renderer.render(scene,camera); frame=requestAnimationFrame(tick); }; tick();
      cleanup=()=>{ cancelAnimationFrame(frame); observer.disconnect(); controls.dispose(); renderer.dispose(); renderer.domElement.remove(); };
    });
    return()=>{disposed=true;cleanup();};
  },[plan]);
  return <div ref={host} className="h-full w-full" aria-label="Interactive 3D bathroom model" />;
}

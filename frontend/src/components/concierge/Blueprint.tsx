import type { StudioPlan } from "@/lib/concierge";
export function Blueprint({plan}:{plan:StudioPlan}){
 const W=520,H=380,p=54, rw=W-p*2,rh=H-p*2;
 return <svg viewBox={`0 0 ${W} ${H}`} className="h-full w-full" role="img" aria-label={`${plan.length} by ${plan.width} foot bathroom blueprint`}>
  <defs><pattern id="grid" width={rw/plan.length} height={rh/plan.width} patternUnits="userSpaceOnUse"><path d={`M ${rw/plan.length} 0 L 0 0 0 ${rh/plan.width}`} className="stroke-blueprint-grid" fill="none" strokeWidth=".65"/></pattern></defs>
  <rect x={p} y={p} width={rw} height={rh} className="fill-blueprint-paper stroke-foreground" strokeWidth="3"/><rect x={p} y={p} width={rw} height={rh} fill="url(#grid)"/>
  {plan.products.map((item,i)=>{const x=p+20+(i%3)*(rw/3),y=p+22+Math.floor(i/3)*(rh/2);return <g key={item.id}><rect x={x} y={y} width={Math.min(78,rw/3-18)} height="56" rx="2" className="fill-background stroke-foreground"/><text x={x+6} y={y+22} className="fill-foreground text-[10px] font-medium">{item.category}</text><text x={x+6} y={y+38} className="fill-muted-foreground text-[8px]">{item.id}</text><rect x={x-8} y={y-8} width={Math.min(94,rw/3-2)} height="72" rx="12" className="fill-accent/10 stroke-accent" strokeDasharray="5 4"/></g>})}
  <path d={`M ${p+rw-70} ${p+rh} A 70 70 0 0 1 ${p+rw} ${p+rh-70}`} className="fill-none stroke-foreground" strokeDasharray="5 4"/><line x1={p+rw-70} y1={p+rh} x2={p+rw} y2={p+rh} className="stroke-foreground"/>
  <line x1={p} y1={H-22} x2={p+rw} y2={H-22} className="stroke-muted-foreground"/><text x={W/2} y={H-9} textAnchor="middle" className="fill-muted-foreground text-[11px]">{plan.length} ft</text>
  <line x1="24" y1={p} x2="24" y2={p+rh} className="stroke-muted-foreground"/><text x="12" y={H/2} textAnchor="middle" transform={`rotate(-90 12 ${H/2})`} className="fill-muted-foreground text-[11px]">{plan.width} ft</text>
 </svg>
}

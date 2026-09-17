import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import { PromptInput, PromptInputFooter, PromptInputSubmit, PromptInputTextarea } from "@/components/ai-elements/prompt-input";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { Button } from "@/components/ui/button";
import { Blueprint } from "./Blueprint";
import { RoomScene } from "./RoomScene";
import { formatINR, loadThreads, makeThread, products, respond, saveThreads, type ChatMessage, type StudioPlan, type Thread } from "@/lib/concierge";
import { Link, useNavigate } from "@tanstack/react-router";
import { Box, Check, ChevronLeft, Menu, Plus, Send, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const QUICK = [
  ["8×6 Modern Bath","Design an 8x6 ft modern bathroom under ₹2,50,000 with matte black fixtures"],
  ["Purist Brass Suite","Recommend a matching Purist faucet and vanity package in Vibrant Moderne Brass with package discount"],
  ["Numi 2.0 Specs","Tell me about the Numi 2.0 smart toilet features, price in INR, and stock availability"],
  ["Zen Spa Master Bath","Design a 10x7 ft luxury zen spa master bathroom under ₹4,00,000 with soaking tub and shower"],
] as const;
const DEFAULT_PLAN: StudioPlan = { length:8,width:6,budget:250000,style:'Modern Minimalist',roomType:'Standard Bath',products:[],discountRate:0,subtotal:0,discounted:0,gst:0,total:0,checks:[
 {label:'Toilet centerline',pass:true,detail:'Minimum 15 in from side wall'}, {label:'Front clearance',pass:true,detail:'Minimum 21 in clear'}, {label:'Door swing arc',pass:true,detail:'30 in unobstructed arc'}, {label:'Within budget',pass:true,detail:'Awaiting specification'}]};

export function ConciergeApp({ threadId }: { threadId: string }) {
  const navigate=useNavigate(); const inputRef=useRef<HTMLTextAreaElement>(null);
  const [threads,setThreads]=useState<Thread[]>([]); const [ready,setReady]=useState(false); const [sending,setSending]=useState(false); const [tab,setTab]=useState<'3d'|'2d'|'specs'>('3d'); const [drawer,setDrawer]=useState(false);
  useEffect(()=>{ const stored=loadThreads(); const exists=stored.find(t=>t.id===threadId); const next=exists?stored:[...stored,{...makeThread(),id:threadId}]; setThreads(next); saveThreads(next); setReady(true); },[threadId]);
  const active=threads.find(t=>t.id===threadId); const plan=active?.plan ?? DEFAULT_PLAN;
  const commit=useCallback((fn:(t:Thread)=>Thread)=>{ setThreads(prev=>{ const next=prev.map(t=>t.id===threadId?fn(t):t); saveThreads(next); return next; }); },[threadId]);
  const send=useCallback((text:string)=>{
    const clean=text.trim();
    if(!clean||sending)return;
    const user:ChatMessage={id:crypto.randomUUID(),role:'user',text:clean};
    commit(t=>({...t,title:t.messages.length<=1?clean.slice(0,34):t.title,updatedAt:Date.now(),messages:[...t.messages,user]}));
    setSending(true);

    fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: clean, thread_id: threadId })
    })
      .then(res => {
        if (!res.ok) throw new Error('API error');
        return res.json();
      })
      .then(data => {
        const answer: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          text: data.text,
          productIds: data.productIds || [],
          plan: data.plan || undefined
        };
        commit(t => ({
          ...t,
          updatedAt: Date.now(),
          messages: [...t.messages, answer],
          ...(answer.plan ? { plan: answer.plan } : {})
        }));
        if (answer.plan) setTab('2d');
      })
      .catch(() => {
        const answer = respond(clean);
        commit(t => ({
          ...t,
          updatedAt: Date.now(),
          messages: [...t.messages, answer],
          ...(answer.plan ? { plan: answer.plan } : {})
        }));
        if (answer.plan) setTab('2d');
      })
      .finally(() => {
        setSending(false);
        window.setTimeout(() => inputRef.current?.focus(), 0);
      });
  },[commit,sending,threadId]);
  const newThread=()=>{const t=makeThread(); const next=[t,...threads]; saveThreads(next); setThreads(next); setDrawer(false); navigate({to:'/chat/$threadId',params:{threadId:t.id}});};
  const deleteThread=(id:string)=>{ const next=threads.filter(t=>t.id!==id); if(next.length===0){const fresh=makeThread();saveThreads([fresh]);navigate({to:'/chat/$threadId',params:{threadId:fresh.id}});return;} saveThreads(next);setThreads(next);if(id===threadId)navigate({to:'/chat/$threadId',params:{threadId:next[0]?.id ?? threadId}});};
  const clear=()=>commit((t)=>{ const { plan: _plan, ...rest } = t; return {...rest,messages:t.messages.slice(0,1),updatedAt:Date.now()}; });
  const selected=useMemo(()=>plan.products,[plan.products]);
  if(!ready||!active)return <div className="grid min-h-screen place-items-center"><Shimmer>Opening your studio…</Shimmer></div>;
  return <main className="min-h-screen bg-background text-foreground">
   <header className="flex h-16 items-center justify-between border-b border-border px-4 md:px-7">
    <div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="md:hidden" onClick={()=>setDrawer(!drawer)} aria-label="Open conversations"><Menu/></Button><Link to="/" className="font-display text-lg md:text-2xl">Kohler Design Concierge</Link><span className="hidden h-4 w-px bg-border sm:block"/><span className="hidden text-[10px] uppercase tracking-[.18em] text-muted-foreground sm:block">Spatial Studio</span></div>
    <div className="flex items-center gap-4 text-[11px] text-muted-foreground"><span><i className="status-dot"/>Catalog 60</span><span className="hidden sm:inline"><i className="status-dot"/>Local session</span><span className="hidden lg:inline"><i className="status-dot"/>IN · INR</span></div>
   </header>
   <div className="relative grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[45%_55%]">
    <aside className={`${drawer?'flex':'hidden'} absolute inset-y-0 left-0 z-30 w-72 flex-col border-r border-border bg-background p-4 md:flex lg:hidden`}>
      <div className="mb-4 flex items-center justify-between"><span className="font-display text-xl">Conversations</span><Button size="icon" variant="ghost" onClick={()=>setDrawer(false)}><ChevronLeft/></Button></div><ThreadList threads={threads} activeId={threadId} onNew={newThread} onDelete={deleteThread}/>
    </aside>
    <section className="flex min-h-[680px] border-b border-border lg:h-[calc(100vh-4rem)] lg:min-h-0 lg:border-b-0 lg:border-r">
     <div className="hidden w-44 shrink-0 border-r border-border p-3 md:flex md:flex-col"><ThreadList threads={threads} activeId={threadId} onNew={newThread} onDelete={deleteThread}/></div>
     <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex items-baseline justify-between border-b border-border px-5 py-4"><div><p className="font-display text-xl">Design conversation</p><p className="mt-1 text-[11px] text-muted-foreground">Concierge · catalog · space planning</p></div><button type="button" onClick={clear} className="text-xs text-muted-foreground transition-colors hover:text-foreground">Clear</button></div>
      <Conversation className="min-h-0"><ConversationContent className="gap-5 px-5 py-6">
       {active.messages.map(m=><ChatRow key={m.id} message={m}/>) }
       {sending&&<Message from="assistant"><MessageContent className="border-l border-border pl-4"><Shimmer>Considering the room…</Shimmer></MessageContent></Message>}
      </ConversationContent><ConversationScrollButton/></Conversation>
      <div className="border-t border-border px-4 py-3">
       <div className="mb-3 flex gap-2 overflow-x-auto pb-1">{QUICK.map(([label,prompt])=><Button key={label} variant="outline" size="sm" className="shrink-0 font-normal" onClick={()=>send(prompt)}>{label}</Button>)}</div>
       <PromptInput onSubmit={({text})=>send(text)} className="architect-input"><PromptInputTextarea ref={inputRef} autoFocus placeholder="Ask about a fixture, finish, room or budget…" className="min-h-20"/><PromptInputFooter className="justify-between"><span className="text-[10px] uppercase tracking-[.14em] text-muted-foreground">Enter to send</span><PromptInputSubmit disabled={sending} status={sending?'submitted':'ready'} aria-label="Send message"><Send/></PromptInputSubmit></PromptInputFooter></PromptInput>
      </div>
     </div>
    </section>
    <Studio plan={plan} selected={selected} tab={tab} setTab={setTab}/>
   </div>
  </main>;
}

function ThreadList({threads,activeId,onNew,onDelete}:{threads:Thread[];activeId:string;onNew:()=>void;onDelete:(id:string)=>void}){
 return <><Button variant="outline" size="sm" onClick={onNew} className="mb-3 w-full justify-start"><Plus/>New study</Button><div className="space-y-1 overflow-y-auto">{[...threads].sort((a,b)=>b.updatedAt-a.updatedAt).map(t=><div key={t.id} className={`group flex items-center border-l ${t.id===activeId?'border-accent bg-accent-soft':'border-transparent'}`}><Link to="/chat/$threadId" params={{threadId:t.id}} className="min-w-0 flex-1 truncate px-3 py-2 text-xs">{t.title}</Link><button type="button" onClick={()=>onDelete(t.id)} className="mr-1 hidden p-1 text-muted-foreground group-hover:block" aria-label={`Delete ${t.title}`}><X className="size-3"/></button></div>)}</div></>;
}
function ChatRow({message}:{message:ChatMessage}){
 const items=message.productIds?.map(id=>products.find(p=>p.id===id)).filter(Boolean) ?? [];
 return <Message from={message.role}><MessageContent className={message.role==='assistant'?'border-l border-border pl-4':'bg-chat-user text-chat-user-foreground'}><MessageResponse>{message.text}</MessageResponse>{items.length>0&&<div className="mt-3 grid gap-2">{items.map(p=>p&&<div key={p.id} className="corner-ticks border border-border bg-surface px-3 py-3"><div className="flex justify-between gap-4"><div><p className="font-display text-base">{p.name}</p><p className="mt-1 text-[11px] text-muted-foreground">{p.id} · {p.finish}</p></div><p className="shrink-0 text-sm font-medium">{formatINR(p.price)}</p></div><div className="mt-3 flex justify-between border-t border-border pt-2 text-[11px] text-muted-foreground"><span>{p.dimensions.width}′ × {p.dimensions.depth}′</span><span>{p.stock}</span></div></div>)}</div>}</MessageContent></Message>;
}
function Studio({plan,selected,tab,setTab}:{plan:StudioPlan;selected:StudioPlan['products'];tab:'3d'|'2d'|'specs';setTab:(t:'3d'|'2d'|'specs')=>void}){
 const tabs=[['3d','3D View'],['2d','2D Blueprint'],['specs','Specs & Clearances']] as const;
 return <section className="flex min-h-[680px] flex-col bg-studio lg:h-[calc(100vh-4rem)] lg:min-h-0">
  <div className="border-b border-border px-5 py-5 md:px-7"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-[10px] uppercase tracking-[.18em] text-muted-foreground">Working drawing</p><h1 className="mt-1 font-display text-3xl">Spatial Studio</h1></div><Box className="size-5 text-accent"/></div><dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-xs sm:grid-cols-4"><Meta label="Room" value={plan.roomType}/><Meta label="Dimensions" value={`${plan.length} × ${plan.width} ft`}/><Meta label="Finish" value={plan.style}/><Meta label="Budget" value={plan.total?`${formatINR(plan.total)} / ${formatINR(plan.budget)}`:'Awaiting brief'}/></dl></div>
  <nav className="flex gap-5 overflow-x-auto border-b border-border px-5 md:px-7">{tabs.map(([id,label])=><button key={id} type="button" onClick={()=>setTab(id)} className={`whitespace-nowrap border-b-2 py-3 text-xs transition-colors ${tab===id?'border-accent text-foreground':'border-transparent text-muted-foreground hover:text-foreground'}`}>{label}</button>)}</nav>
  <div className={`relative min-h-[420px] flex-1 overflow-hidden ${tab==='2d'?'blueprint-grid':''}`}>
   {tab==='3d'&&<RoomScene plan={plan}/>} {tab==='2d'&&<div className="h-full min-h-[480px] p-5"><Blueprint plan={plan}/></div>} {tab==='specs'&&<Specs plan={plan} selected={selected}/>} 
   {selected.length===0&&tab!=='specs'&&<div className="pointer-events-none absolute bottom-5 left-5 border-l border-accent bg-background/90 px-3 py-2 text-xs text-muted-foreground">Describe your room in the conversation to populate the plan.</div>}
  </div>
 </section>;
}
function Meta({label,value}:{label:string;value:string}){return <div><dt className="text-[9px] uppercase tracking-[.15em] text-muted-foreground">{label}</dt><dd className="mt-1 truncate">{value}</dd></div>}
function Specs({plan,selected}:{plan:StudioPlan;selected:StudioPlan['products']}){return <div className="h-full overflow-auto p-5 md:p-7"><table className="w-full border-collapse text-left text-xs"><thead><tr className="border-b border-foreground"><th className="py-2 font-medium">SKU / fixture</th><th className="py-2 font-medium">Category</th><th className="py-2 text-right font-medium">Price</th></tr></thead><tbody>{selected.map(p=><tr key={p.id} className="border-b border-border"><td className="py-3"><span className="block font-medium">{p.name}</span><span className="text-[10px] text-muted-foreground">{p.id}</span></td><td>{p.category}</td><td className="text-right">{formatINR(p.price)}</td></tr>)}</tbody><tfoot className="font-medium"><tr><td colSpan={2} className="pt-4">Bundle discount ({plan.discountRate*100}%)</td><td className="pt-4 text-right">−{formatINR(plan.subtotal-plan.discounted)}</td></tr><tr><td colSpan={2} className="pt-2">GST (18%)</td><td className="pt-2 text-right">{formatINR(plan.gst)}</td></tr><tr className="font-display text-lg"><td colSpan={2} className="pt-3">Grand total</td><td className="pt-3 text-right">{formatINR(plan.total)}</td></tr></tfoot></table><div className="mt-8 border-t border-border pt-5"><h2 className="font-display text-xl">Clearance review</h2><div className="mt-3 divide-y divide-border">{plan.checks.map(c=><div key={c.label} className="flex items-center gap-3 py-3"><span className="grid size-5 place-items-center border border-border">{c.pass?<Check className="size-3 text-accent"/>:<X className="size-3"/>}</span><div className="flex-1"><p className="text-xs font-medium">{c.label}</p><p className="text-[11px] text-muted-foreground">{c.detail}</p></div></div>)}</div></div></div>}

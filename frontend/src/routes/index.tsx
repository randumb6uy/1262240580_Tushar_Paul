import { loadThreads, makeThread, saveThreads } from "@/lib/concierge";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

export const Route=createFileRoute("/")({
 head:()=>({meta:[{title:"Kohler Design Concierge & Spatial Studio"},{name:"description",content:"Explore Kohler bathroom fixtures and create budget-aware spatial plans in an interactive design studio."},{property:"og:title",content:"Kohler Design Concierge & Spatial Studio"},{property:"og:description",content:"Explore Kohler bathroom fixtures and create budget-aware spatial plans in an interactive design studio."},{property:"og:type",content:"website"},{name:"twitter:card",content:"summary_large_image"}]}), component:Index});
function Index(){const navigate=useNavigate();useEffect(()=>{const current=loadThreads();const first=current[0]??makeThread();if(!current.length)saveThreads([first]);navigate({to:'/chat/$threadId',params:{threadId:first.id},replace:true});},[navigate]);return <div className="grid min-h-screen place-items-center font-display text-xl">Opening the studio…</div>}

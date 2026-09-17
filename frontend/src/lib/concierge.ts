import catalog from "@/data/products.json";

export type Product = (typeof catalog)[number];
export type StudioPlan = {
  length: number; width: number; budget: number; style: string; roomType: string;
  products: Product[]; discountRate: number; subtotal: number; discounted: number; gst: number; total: number;
  checks: { label: string; pass: boolean; detail: string }[];
};
export type ChatMessage = { id: string; role: "user" | "assistant"; text: string; productIds?: string[]; plan?: StudioPlan };
export type Thread = { id: string; title: string; updatedAt: number; messages: ChatMessage[]; plan?: StudioPlan };

export const products = catalog as Product[];
export const formatINR = (value: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
export const discountFor = (count: number) => count >= 6 ? .22 : count >= 4 ? .18 : count === 3 ? .15 : count === 2 ? .1 : 0;

const initialGreeting: ChatMessage = { id: "welcome", role: "assistant", text: "Welcome. I’m your Kohler design concierge. Tell me about your room, budget, or a fixture you’re considering, and I’ll compose a considered scheme." };
export const makeThread = (): Thread => ({ id: crypto.randomUUID(), title: "New bathroom study", updatedAt: Date.now(), messages: [initialGreeting] });
export const loadThreads = (): Thread[] => {
  if (typeof window === "undefined") return [];
  try { return JSON.parse(localStorage.getItem("kohler-studio-threads") ?? "[]") as Thread[]; } catch { return []; }
};
export const saveThreads = (threads: Thread[]) => localStorage.setItem("kohler-studio-threads", JSON.stringify(threads));

export function searchProducts(query: string) {
  const q = query.toLowerCase();
  return products.filter((p) => [p.name,p.category,p.finish,p.style,...p.features].some((x) => x.toLowerCase().includes(q))).slice(0,4);
}

export function optimize(input: string): StudioPlan {
  const dims = input.match(/(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)/i);
  const money = input.replaceAll(",", "").match(/₹\s*(\d+)/);
  const length = Number(dims?.[1] ?? 8), width = Number(dims?.[2] ?? 6), budget = Number(money?.[1] ?? 250000);
  const area = length * width;
  const roomType = area <= 32 ? "Powder Room" : area <= 58 ? "Standard Bath" : "Master Suite";
  const style = /zen|spa/i.test(input) ? "Zen Spa" : /heritage|traditional/i.test(input) ? "Heritage Traditional" : /industrial/i.test(input) ? "Industrial Luxury" : /tech|smart|futur/i.test(input) ? "High-Tech Futuristic" : "Modern Minimalist";
  const wanted = /tub|soaking/i.test(input) ? ["Tub","Shower","Toilet","Faucet"] : roomType === "Powder Room" ? ["Toilet","Sink","Faucet"] : ["Toilet","Vanity","Faucet","Shower"];
  const pool = products.filter((p) => wanted.includes(p.category)).sort((a,b) => a.price-b.price);
  const chosen: Product[] = [];
  for (const category of wanted) {
    const matches = pool.filter((p) => p.category === category && (p.style === style || p.finish.toLowerCase().includes(input.toLowerCase().includes("black") ? "black" : "zz")));
    const item = matches[0] ?? pool.find((p) => p.category === category);
    if (item) chosen.push(item);
  }
  let subtotal = chosen.reduce((sum,p) => sum+p.price,0), rate = discountFor(chosen.length);
  while (chosen.length > 1 && subtotal * (1-rate) * 1.18 > budget) { chosen.pop(); subtotal = chosen.reduce((sum,p) => sum+p.price,0); rate = discountFor(chosen.length); }
  const discounted = Math.round(subtotal*(1-rate)), gst = Math.round(discounted*.18), total = discounted+gst;
  const spacious = width >= 5 && length >= 6;
  return { length,width,budget,style,roomType,products:chosen,discountRate:rate,subtotal,discounted,gst,total,checks:[
    {label:'Toilet centerline',pass:width>=4,detail:'Minimum 15 in from side wall'},
    {label:'Front clearance',pass:length>=5,detail:'Minimum 21 in clear'},
    {label:'Door swing arc',pass:spacious,detail:'30 in unobstructed arc'},
    {label:'Within budget',pass:total<=budget,detail:`${formatINR(Math.abs(budget-total))} ${total<=budget?'remaining':'over'}`},
  ]};
}

export function deliveryEstimate(pin: string) {
  if (/^400001/.test(pin)) return "Mumbai · 1–2 business days";
  if (/^110001/.test(pin)) return "Delhi NCR · 2–3 business days";
  if (/^560001/.test(pin)) return "Bengaluru · 2–3 business days";
  return "Rest of India · 4–6 business days";
}

export function respond(input: string): ChatMessage {
  const q=input.toLowerCase();
  if (/\b(hi|hello|hey|namaste)\b/.test(q)) return {id:crypto.randomUUID(),role:'assistant',text:'Good day. I can help you select a single fixture or plan an entire bathroom around your space and budget.'};
  if (/\b\d{6}\b/.test(q)) { const pin=q.match(/\b\d{6}\b/)?.[0] ?? ''; return {id:crypto.randomUUID(),role:'assistant',text:`Estimated delivery: **${deliveryEstimate(pin)}**. Availability is confirmed at order placement.`}; }
  if (/design|bathroom|budget|under ₹|under rs|room/i.test(input) && (/\d\s*[x×]\s*\d/i.test(input) || /budget|under/i.test(input))) {
    const plan=optimize(input); return {id:crypto.randomUUID(),role:'assistant',text:`I’ve composed a **${plan.roomType}** in the **${plan.style}** family. The ${plan.products.length}-piece edit totals **${formatINR(plan.total)} including GST**, ${plan.total<=plan.budget?'within':'above'} your ${formatINR(plan.budget)} budget. The studio has been updated.`,productIds:plan.products.map(p=>p.id),plan};
  }
  const matches=searchProducts(q.replace(/tell me about|recommend|specs|features|price|stock|availability|package|matching/gi,'').trim());
  const fallback = products.filter((p) => {
    const firstWord = p.name.split(' ')[0];
    return firstWord ? q.includes(firstWord.toLowerCase()) : false;
  }).slice(0,4);
  const found=matches.length?matches:fallback;
  if(found.length){ const rate=discountFor(found.length); return {id:crypto.randomUUID(),role:'assistant',text:`I found ${found.length===1?'a focused specification':'a coordinated selection'}. ${rate?`A **${rate*100}% bundle consideration** applies to these ${found.length} pieces.`:'Ask for a matching suite to explore package pricing.'}`,productIds:found.map(p=>p.id)}; }
  return {id:crypto.randomUUID(),role:'assistant',text:'I can narrow the catalog by fixture, finish, style, budget, or room dimensions. Try “Purist brass faucet” or share a room size such as 8×6 ft.'};
}

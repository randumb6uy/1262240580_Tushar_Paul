import { ConciergeApp } from "@/components/concierge/ConciergeApp";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/chat/$threadId")({
 head:()=>({meta:[{title:"Bathroom Spatial Studio — Kohler Concierge"},{name:"description",content:"Plan a Kohler bathroom with fixture recommendations, budget optimization, and interactive spatial drawings."},{property:"og:title",content:"Bathroom Spatial Studio — Kohler Concierge"},{property:"og:description",content:"Plan a Kohler bathroom with fixture recommendations, budget optimization, and interactive spatial drawings."},{property:"og:type",content:"website"},{name:"twitter:card",content:"summary_large_image"}]}),
 component:Page,
});
function Page(){const {threadId}=Route.useParams();return <ConciergeApp key={threadId} threadId={threadId}/>}

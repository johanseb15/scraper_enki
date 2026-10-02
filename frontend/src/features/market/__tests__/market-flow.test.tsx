import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import MarketPage from "@/features/market/MarketPage";

const group = {currency:"ARS",modality:"remoto",unit:"hora",scope:"Soporte por una hora",
  offer_count:1,provider_count:1,min:"1299.50",median:"1299.50",max:"1299.50",
  own_price_difference_pct:null,evidence_ids:["a"]};
const response = {service:"soporte_tecnico",offer_count:1,provider_count:1,benchmarks:[group],
  offers:[{id:"a",provider:"Proveedor observado",service:"soporte_tecnico",price:"1299.50",currency:"ARS",
    modality:"remoto",unit:"hora",scope:group.scope,province:null,city:null,source_url:"https://provider.example/precio",
    captured_at:"2026-10-02T14:00:00Z",effective_date:null,capture_url:"/market/captures/public",
    raw:{servicio_raw:"Soporte técnico",precio_raw:"$1.299,50",source_excerpt:"Soporte técnico $1.299,50"},exclusion_reason:null,
    comparability_note:"Una hora publicada"}],
  hypotheses:[{title:"Validar alcance",reason:"Una oferta observada",next_step:"Solicitar cotización",evidence_ids:["a"]}],
  unanswered:["Demanda y rentabilidad"],limitations:["No representa todo el mercado argentino."]};

beforeEach(()=>vi.stubGlobal("fetch",vi.fn(async (url:string, options?:RequestInit)=> {
  if(url.endsWith("/catalog")) return {ok:true,json:async()=>({services:[{id:"soporte_tecnico",label:"Soporte técnico",category:"Soporte"},
    {id:"soporte_redes",label:"Soporte de redes",category:"Conectividad"}],cities:[],provinces:[],currencies:["ARS"],modalities:["remoto"],capture_count:1,observation_count:1})};
  const body=JSON.parse(String(options?.body));
  const result=body.service==="soporte_redes"?{...response,offer_count:0,provider_count:0,offers:[],benchmarks:[],hypotheses:[]}:
    body.own_price?{...response,benchmarks:[{...group,own_price_difference_pct:"0.00"}]}:response;
  return {ok:true,json:async()=>result};
})));
afterEach(()=>vi.unstubAllGlobals());

test("recorrido completo conserva texto del precio, fuentes y contexto",async()=>{
  const user=userEvent.setup();render(<MarketPage/>);
  expect(await screen.findByText("Proveedor observado")).toBeInTheDocument();
  expect(screen.getByLabelText("Alcance seleccionado")).toHaveTextContent(group.scope);
  expect(screen.getByText("ARS 1.299,50",{selector:"strong"})).toBeInTheDocument();
  expect(screen.getByRole("link",{name:"Abrir fuente pública"})).toHaveAttribute("href","https://provider.example/precio");
  expect(screen.getByRole("link",{name:"Abrir captura guardada"})).toHaveAttribute("href",expect.stringContaining("/market/captures/public"));
  await user.type(screen.getByLabelText("Tu precio"),"1.299,50");
  await user.click(screen.getByRole("button",{name:"Comparar mi precio"}));
  expect(await screen.findByText(/0,00%/)).toBeInTheDocument();
  const calls=vi.mocked(fetch).mock.calls;
  const body=JSON.parse(String(calls[calls.length-1][1]?.body));
  expect(body.own_price).toBe("1.299,50");expect(body.own_scope).toBe(group.scope);
  expect(screen.getByText("Demanda y rentabilidad")).toBeInTheDocument();
  await user.click(screen.getByRole("button",{name:"Restablecer caso"}));
  await waitFor(()=>expect(screen.getByLabelText("Tu precio")).toHaveValue(""));
});

test("filtros muestran estado vacío y permiten volver al caso",async()=>{
  const user=userEvent.setup();render(<MarketPage/>);
  await screen.findByText("Proveedor observado");
  await user.selectOptions(screen.getByLabelText("Servicio"),"soporte_redes");
  await user.click(screen.getByRole("button",{name:"Consultar evidencia"}));
  expect(await screen.findByText("Todavía no hay evidencia para esta consulta")).toBeInTheDocument();
  await user.click(screen.getByRole("button",{name:"Restablecer caso"}));
  expect(await screen.findByText("Proveedor observado")).toBeInTheDocument();
});

test("errores de conexión visibles y reintento",async()=>{
  vi.stubGlobal("fetch",vi.fn().mockRejectedValue(new Error("sin conexión")));
  render(<MarketPage/>);
  expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cargar");
  expect(screen.getByRole("button",{name:"Reintentar"})).toBeInTheDocument();
});

test("estado de carga explícito",()=>{
  vi.stubGlobal("fetch",vi.fn(()=>new Promise(()=>{})));
  render(<MarketPage/>);
  expect(screen.getByRole("status")).toHaveTextContent("Cargando evidencia");
});

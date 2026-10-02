"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { Benchmark, Catalog, Filters, MarketResult } from "./types";
import styles from "./market.module.css";

const api = process.env.NEXT_PUBLIC_ENKI_API_URL ?? "http://127.0.0.1:8000";
const defaults:Filters = {service:"soporte_tecnico",city:"",province:"",currency:"",modality:""};
const money = (value:string, currency:string) => {
  const [integer, decimals="00"]=value.split(".");
  return `${currency} ${integer.replace(/\B(?=(\d{3})+(?!\d))/g,".")},${decimals}`;
};
const date = (value:string|null) => value ? new Date(value).toLocaleString("es-AR") : "Desconocida";

async function request<T>(path:string, signal:AbortSignal, body?:unknown):Promise<T> {
  const response = await fetch(`${api}${path}`,{signal,...(body?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}:{})});
  if(!response.ok) {
    const error=await response.json().catch(()=>null);
    throw new Error(typeof error?.detail==="string"?error.detail:"Revisá los filtros y el precio ingresado.");
  }
  return response.json();
}

export default function MarketPage() {
  const [catalog,setCatalog]=useState<Catalog|null>(null);
  const [filters,setFilters]=useState<Filters>(defaults);
  const [appliedFilters,setAppliedFilters]=useState<Filters>(defaults);
  const [result,setResult]=useState<MarketResult|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [ownPrice,setOwnPrice]=useState("");
  const [selectedGroup,setSelectedGroup]=useState(0);
  const [comparison,setComparison]=useState<{price:string;scope:string}|null>(null);
  const controller=useRef<AbortController|null>(null);

  async function load(next:Filters=defaults, compare?:Benchmark) {
    controller.current?.abort();
    const active=new AbortController();controller.current=active;
    const timeout=setTimeout(()=>active.abort(),12000);
    setLoading(true);setError("");
    try {
      const payload={...next,city:next.city||null,province:next.province||null,currency:next.currency||null,modality:next.modality||null,
        ...(compare?{own_price:ownPrice,own_currency:compare.currency,own_modality:compare.modality,own_unit:compare.unit,own_scope:compare.scope}:{})};
      const [meta,data]=await Promise.all([
        catalog ? Promise.resolve(catalog) : request<Catalog>("/market/catalog",active.signal),
        request<MarketResult>("/market/query",active.signal,payload),
      ]);
      if(controller.current!==active)return;
      setCatalog(meta);setResult(data);setAppliedFilters(next);
      setComparison(compare?{price:ownPrice,scope:compare.scope}:null);
      if(!compare)setSelectedGroup(0);
    } catch(e) {
      if(controller.current!==active)return;
      setError(`No se pudo cargar la consulta. ${e instanceof Error && e.name!=="AbortError"?e.message:"El servidor tardó demasiado; reintentá."}`);
    } finally {
      clearTimeout(timeout);
      if(controller.current===active)setLoading(false);
    }
  }

  useEffect(()=>{
    const active=new AbortController();controller.current=active;
    const timeout=setTimeout(()=>active.abort(),12000);
    Promise.all([request<Catalog>("/market/catalog",active.signal),
      request<MarketResult>("/market/query",active.signal,{service:defaults.service})])
      .then(([meta,data])=>{if(controller.current===active){setCatalog(meta);setResult(data);}})
      .catch(e=>{if(controller.current===active)setError(`No se pudo cargar la consulta. ${e.name==="AbortError"?"El servidor tardó demasiado; reintentá.":e.message}`);})
      .finally(()=>{clearTimeout(timeout);if(controller.current===active)setLoading(false);});
    return()=>{clearTimeout(timeout);controller.current?.abort();controller.current=null;};
  },[]);

  function reset(){setFilters(defaults);setOwnPrice("");setComparison(null);void load(defaults);}
  const group=result?.benchmarks[selectedGroup];
  const serviceLabel=catalog?.services.find(s=>s.id===result?.service)?.label??"Competencia observada";

  return <main className={styles.page}>
    <header className={styles.header}>
      <Link className={styles.brand} href="/">enki<span>Inteligencia para decidir</span></Link>
      <nav aria-label="Navegación principal"><Link aria-current="page" href="/mercado">Mercado</Link><Link href="/cotizacion">Revisar cotización</Link></nav>
      <span className={styles.offline}><i/> Evidencia guardada · offline</span>
    </header>
    <div className={styles.container}>
      <section className={styles.hero}>
        <div><p className={styles.eyebrow}>ENKI MARKET / ARGENTINA</p><h1>Conocé la muestra.<br/>Decidí qué investigar.</h1>
          <p>Proveedores, precios publicados y señales comerciales, con la evidencia a un clic.</p></div>
        <div className={styles.heroNote}><span className={styles.noteMark}>↗</span><b>Una mirada fundamentada</b>
          <p>Muestra pequeña y dirigida. Cada cifra tiene fuente; cada hipótesis requiere validación.</p>
          <small>{catalog?`${catalog.capture_count} capturas públicas · ${catalog.observation_count} observaciones` : "Consultando las capturas guardadas"}</small></div>
      </section>
      <div className={styles.workspace}>
        <aside className={styles.sidebar}>
          <p className={styles.eyebrow}>01 / DEFINÍ EL CASO</p><h2>Qué querés investigar</h2>
          <form onSubmit={e=>{e.preventDefault();setOwnPrice("");setComparison(null);void load(filters);}}>
            <label>Servicio<select value={filters.service} disabled={!catalog||loading} onChange={e=>setFilters({...filters,service:e.target.value})}>
              {catalog?.services.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}
            </select></label>
            <label>Ubicación publicada<select value={filters.city} disabled={!catalog||loading} onChange={e=>setFilters({...filters,city:e.target.value})}>
              <option value="">Todas las ubicaciones</option>{catalog?.cities.map(c=><option key={c}>{c}</option>)}
            </select></label>
            <p className={styles.help}>Ubicación del proveedor; la cobertura de atención puede ser desconocida.</p>
            <label>Moneda<select value={filters.currency} disabled={!catalog||loading} onChange={e=>setFilters({...filters,currency:e.target.value})}>
              <option value="">Grupos separados</option><option>ARS</option><option>USD</option>
            </select></label>
            <label>Modalidad<select value={filters.modality} disabled={!catalog||loading} onChange={e=>setFilters({...filters,modality:e.target.value})}>
              <option value="">Todas</option>{catalog?.modalities.map(m=><option key={m}>{m}</option>)}
            </select></label>
            <button className={styles.primary} disabled={loading||!catalog} type="submit">Consultar evidencia <span aria-hidden="true">→</span></button>
          </form>
          <button className={styles.reset} disabled={loading} onClick={reset}><span aria-hidden="true">↺</span> <span>Restablecer caso</span></button>
          <div className={styles.sidebarNote}><b>Leer precios con contexto</b><p>No se mezclan monedas, modalidades ni alcances distintos. Los faltantes permanecen desconocidos.</p></div>
        </aside>
        <div className={styles.content} aria-busy={loading}>
          {loading&&<div role="status" className={styles.loading}><span/>Cargando evidencia…</div>}
          {error&&<div className={styles.error} role="alert"><b>{error}</b><button onClick={()=>void load(appliedFilters)}>Reintentar</button></div>}
          {result&&!loading&&!error&&<>
            <section className={styles.section}>
              <div className={styles.sectionHeading}><div><p className={styles.eyebrow}>02 / COMPETENCIA OBSERVADA</p><h2>{serviceLabel}</h2></div><span className={styles.pill}>Fuentes públicas</span></div>
              <div className={styles.metrics}><div><strong>{result.provider_count}</strong><span>proveedores observados</span></div><div><strong>{result.offer_count}</strong><span>ofertas observadas</span></div><div><strong>{result.benchmarks.length}</strong><span>grupos con precios admisibles</span></div></div>
              {!result.offer_count?<div className={styles.empty}><span>◎</span><h3>Todavía no hay evidencia para esta consulta</h3><p>La muestra guardada no contiene ofertas con esos filtros. No se infiere ausencia de competencia.</p><button onClick={reset}>Volver al caso inicial</button></div>:
              <div className={styles.offerList}>{result.offers.map(o=><article className={styles.offer} id={`evidence-${o.id}`} key={o.id}>
                <div className={styles.offerTop}><div><h3>{o.provider}</h3><p>{o.raw.servicio_raw}</p></div><div className={styles.price}><strong>{o.price?money(o.price,o.currency??"Moneda desconocida"):o.raw.precio_raw}</strong><small>{o.unit??"Unidad no declarada"}</small></div></div>
                <div className={styles.tags}><span>{o.city??o.province??"Ubicación sin precisar"}</span><span>{o.modality??"Modalidad desconocida"}</span><span className={o.exclusion_reason?styles.excluded:styles.admitted}>{o.exclusion_reason?"Fuera del benchmark":"Referencia admisible"}</span></div>
                {o.exclusion_reason&&<p className={styles.exclusion}>Motivo: {o.exclusion_reason}.</p>}
                <div className={styles.sourceLine}><span>Captura: {date(o.captured_at)}</span><span>Fecha efectiva: {o.effective_date??"Desconocida"}</span></div>
                <div className={styles.links}><a href={o.source_url} target="_blank" rel="noreferrer">Abrir fuente pública <span aria-hidden="true">↗</span></a>{o.capture_url&&<a href={`${api}${o.capture_url}`} target="_blank" rel="noreferrer">Abrir captura guardada <span aria-hidden="true">↗</span></a>}</div>
                <details><summary>Ver evidencia y condiciones</summary><p>{o.comparability_note??"Sin información adicional."}</p><blockquote>{o.raw.source_excerpt}</blockquote><small>Precio original: {o.raw.precio_raw} · ID: {o.id}</small></details>
              </article>)}</div>}
            </section>
            <section className={styles.section}>
              <p className={styles.eyebrow}>03 / BENCHMARK Y TU PRECIO</p><h2>Compará el mismo alcance</h2>
              {group?<>
                <label className={styles.groupLabel}>Grupo comparable<select value={selectedGroup} onChange={e=>{setSelectedGroup(Number(e.target.value));setComparison(null);}}>{result.benchmarks.map((g,i)=><option key={`${g.scope}-${g.currency}`} value={i}>{g.scope} · {g.currency}</option>)}</select></label>
                <p className={styles.context} aria-label="Alcance seleccionado">{group.scope}</p>
                <p className={styles.context}>{group.modality} · por {group.unit} · {group.offer_count} oferta{group.offer_count===1?"":"s"} de {group.provider_count} proveedor{group.provider_count===1?"":"es"}</p>
                {group.provider_count===1&&<p className={styles.caution}>Referencia individual. Esta mediana describe un solo proveedor.</p>}
                <div className={styles.benchmark}><div><span>Mínimo observado</span><b>{money(group.min,group.currency)}</b></div><div className={styles.median}><span>Mediana observada</span><b>{money(group.median,group.currency)}</b></div><div><span>Máximo observado</span><b>{money(group.max,group.currency)}</b></div></div>
                <form className={styles.ownForm} onSubmit={e=>{e.preventDefault();void load(appliedFilters,group);}}>
                  <label>Tu precio<div className={styles.moneyInput}><span>{group.currency}</span><input aria-label="Tu precio" value={ownPrice} onChange={e=>{setOwnPrice(e.target.value);setComparison(null);}} required inputMode="decimal" placeholder="35.000,50" maxLength={40}/></div></label>
                  <button className={styles.primary} type="submit">Comparar mi precio</button>
                </form>
                <p className={styles.help}>Al comparar, indicás que tu precio cubre el alcance, la moneda, la modalidad y la unidad del grupo elegido.</p>
                {comparison&&comparison.scope===group.scope&&group.own_price_difference_pct!==null&&<div className={styles.comparison} role="status"><b>{group.own_price_difference_pct.replace(".",",")}% respecto de la mediana</b><p>Tu precio: {comparison.price} {group.currency}. La diferencia es descriptiva; no evalúa rentabilidad ni calidad.</p></div>}
              </>:<div className={styles.noBenchmark}>No hay precios admisibles para un benchmark con estos filtros. Revisá los motivos de exclusión en las ofertas.</div>}
            </section>
            <section className={styles.section}><p className={styles.eyebrow}>04 / HIPÓTESIS COMERCIALES</p><h2>Preguntas que merece la pena investigar</h2>
              <p className={styles.context}>Hipótesis fundamentadas; requieren validación con proveedores y clientes.</p>
              <div className={styles.hypotheses}>{result.hypotheses.map((h,i)=><article key={i}><span className={styles.hypothesisNumber}>{String(i+1).padStart(2,"0")}</span><div><h3>{h.title}</h3><p>{h.reason}</p><b>Próximo paso</b><p>{h.next_step}</p><div className={styles.evidenceRefs}>{h.evidence_ids.map(id=><a href={`#evidence-${id}`} key={id}>Ver evidencia {id} ↑</a>)}</div></div></article>)}</div>
              {!result.hypotheses.length&&<p>Hace falta incorporar evidencia verificable antes de proponer hipótesis.</p>}
            </section>
            <section className={styles.limits}><div><p className={styles.eyebrow}>LO QUE TODAVÍA NO SABEMOS</p><h2>Los límites también son información</h2><ul>{result.unanswered.map(item=><li key={item}>{item}</li>)}</ul></div><div><h3>Cómo leer esta muestra</h3>{result.limitations.map(item=><p key={item}>{item}</p>)}</div></section>
          </>}
        </div>
      </div>
      <footer className={styles.footer}><b>enki</b><span>Evidencia pública, decisiones informadas. Argentina · Demo comercial</span></footer>
    </div>
  </main>;
}

export type Catalog = {
  services: {id:string;label:string;category:string}[];
  provinces:string[];cities:string[];currencies:string[];modalities:string[];
  capture_count:number;observation_count:number;
};
export type Benchmark = {
  currency:string;modality:string;unit:string;scope:string;
  offer_count:number;provider_count:number;min:string;median:string;max:string;
  own_price_difference_pct:string|null;evidence_ids:string[];
};
export type Offer = {
  id:string;provider:string;service:string;price:string|null;currency:string|null;
  modality:string|null;unit:string|null;scope:string|null;province:string|null;city:string|null;
  source_url:string;captured_at:string|null;effective_date:string|null;capture_url:string|null;
  raw:{servicio_raw:string;precio_raw:string;source_excerpt:string};
  exclusion_reason:string|null;comparability_note:string|null;
};
export type MarketResult = {
  service:string;offer_count:number;provider_count:number;offers:Offer[];benchmarks:Benchmark[];
  hypotheses:{title:string;reason:string;next_step:string;evidence_ids:string[]}[];
  unanswered:string[];limitations:string[];
};
export type Filters = {service:string;city:string;province:string;currency:string;modality:string};

from __future__ import annotations
import re, unicodedata
from src.dominio.semantic_observation import ScopeMeaning, ScopeMeaningKind, SemanticObservation, SemanticObservationRole

def interpret_scope_meaning(observation: SemanticObservation) -> ScopeMeaning:
    if observation.semantic_role is not SemanticObservationRole.SCOPE_DEVICE:
        raise ValueError('interpret_scope_meaning requires a SCOPE_DEVICE observation.')
    raw=observation.raw_expression; f=_fold(raw)
    m=re.search(r'\bhasta\s+(\d+(?:[.,]\d+)?)\s*(gb|tb)\b',f)
    if m:
        return ScopeMeaning(raw,ScopeMeaningKind.DATA_CAPACITY_BAND,observation.interpretation_provenance,capacity_max_value=float(m.group(1).replace(',','.')),capacity_unit=m.group(2).upper())
    modes=tuple(x for x,p in [('FREELANCE',r'\bfreelance\b'),('WORKSHOP',r'\btaller\b')] if re.search(p,f))
    if modes:
        return ScopeMeaning(raw,ScopeMeaningKind.PROVIDER_DELIVERY_CONTEXT,observation.interpretation_provenance,delivery_modes=modes)
    dev=[]
    if re.search(r'\bnotebook\b|\blaptop\b',f): dev.append('NOTEBOOK')
    if re.search(r'\baio\b|all[\s-]?in[\s-]?one',f): dev.append('AIO')
    if re.search(r'\bpc\b|\bcomputadora\b',f): dev.append('PC')
    tiers=[]
    if re.search(r'\bgama media/alta\b|\bgama media alta\b',f): tiers.append('MID_HIGH')
    elif re.search(r'\bgama media\b',f): tiers.append('MID')
    for p,v in [(r'\bbasica\b|\bbasico\b','BASIC'),(r'\bgamer\b','GAMER'),(r'\bestandar\b','STANDARD'),(r'\bantigua\b','LEGACY'),(r'\bintegrados?\b','INTEGRATED'),(r'\bpro\b','PRO'),(r'\bultra\b|\bpremium\b','PREMIUM')]:
        if re.search(p,f): tiers.append(v)
    dev=tuple(dict.fromkeys(dev)); tiers=tuple(dict.fromkeys(tiers))
    if dev: return ScopeMeaning(raw,ScopeMeaningKind.DEVICE_PROFILE,observation.interpretation_provenance,device_types=dev,tiers=tiers)
    if tiers: return ScopeMeaning(raw,ScopeMeaningKind.TIER_ONLY,observation.interpretation_provenance,tiers=tiers)
    return ScopeMeaning(raw,ScopeMeaningKind.UNKNOWN,observation.interpretation_provenance)

def _fold(t):
    n=unicodedata.normalize('NFKD',t or '')
    return ' '.join(''.join(c for c in n if not unicodedata.combining(c)).lower().split())

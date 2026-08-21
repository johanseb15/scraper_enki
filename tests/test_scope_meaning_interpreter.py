import pytest
from src.dominio.semantic_knowledge import KnowledgeProvenance
from src.dominio.semantic_observation import ScopeMeaningKind,ScopeUnderstandingStatus,SemanticObservation,SemanticObservationRole
from src.infraestructura.scope_meaning_interpreter import interpret_scope_meaning

def p(k='SEMANTIC_NORMALIZATION',r='semantic.csv'): return KnowledgeProvenance(k,r,'v1')
def scope(raw): return SemanticObservation('1',raw,SemanticObservationRole.SCOPE_DEVICE,'NONE','provider_a','Provider A','Córdoba',p('COMMERCIAL_OBSERVATION','row:1'),p())
def test_device():
    m=interpret_scope_meaning(scope('PC Gamer gama media')); assert m.meaning_kind is ScopeMeaningKind.DEVICE_PROFILE and m.device_types==('PC',) and m.tiers==('MID','GAMER') and m.understanding_status is ScopeUnderstandingStatus.UNDERSTOOD
def test_notebook(): assert interpret_scope_meaning(scope('Notebook básica')).device_types==('NOTEBOOK',)
def test_aio(): assert interpret_scope_meaning(scope('AIO estándar')).device_types==('AIO',)
def test_tier():
    m=interpret_scope_meaning(scope('Gama Media/alta')); assert m.meaning_kind is ScopeMeaningKind.TIER_ONLY and m.tiers==('MID_HIGH',)
def test_capacity():
    m=interpret_scope_meaning(scope('hasta 500gb')); assert m.meaning_kind is ScopeMeaningKind.DATA_CAPACITY_BAND and m.capacity_max_value==500 and m.capacity_unit=='GB'
def test_tb_no_conversion():
    m=interpret_scope_meaning(scope('hasta 4tb')); assert m.capacity_max_value==4 and m.capacity_unit=='TB'
def test_delivery():
    m=interpret_scope_meaning(scope('Freelance / taller')); assert m.meaning_kind is ScopeMeaningKind.PROVIDER_DELIVERY_CONTEXT and m.delivery_modes==('FREELANCE','WORKSHOP')
def test_unknown(): assert interpret_scope_meaning(scope('contexto no identificado')).understanding_status is ScopeUnderstandingStatus.UNKNOWN
def test_raw_provenance():
    o=scope('PC Gamer Integrados/Básica'); m=interpret_scope_meaning(o); assert m.source_expression==o.raw_expression and m.provenance==o.interpretation_provenance
def test_reject_non_scope():
    o=scope('PC'); object.__setattr__(o,'semantic_role',SemanticObservationRole.PRICE_CONTEXT)
    with pytest.raises(ValueError): interpret_scope_meaning(o)
def test_no_service_invention(): assert scope('PC Gamer').canonical_service is None

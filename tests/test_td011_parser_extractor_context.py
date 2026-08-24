from __future__ import annotations
import pytest
from src.aplicacion.language_query_contract import PriceType
from src.aplicacion.parser_consulta_pricing import parse_pricing_query
from src.dominio.offer_evidence import ChargedUnit, PriceBound
from src.dominio.price_scope_contract import PriceBoundMeaning, normalize_price_scope
from src.infraestructura.offer_evidence_extractor import extract_claims_from_explicit_basis
from src.infraestructura.price_context_interpreter import _price_scope

def _claims(text):
    return extract_claims_from_explicit_basis(observation_id='td011',raw_basis=text,raw_document_id='sha256:td011',provenance='td011-test')
def _values(text,dimension): return {c.value for c in _claims(text) if c.dimension==dimension}

@pytest.mark.parametrize(('text','expected_type','expected_scope'),(
('35 lucas por hora',PriceType.PER_HOUR,'PER_HOUR'),('35 lucas hora adicional',PriceType.PER_HOUR,'PER_HOUR'),('35 lucas por mes',PriceType.PER_MONTH,'PER_MONTH'),('35 lucas por visita',PriceType.PER_VISIT,'PER_VISIT'),('35 lucas por equipo',PriceType.PER_UNIT,'PER_UNIT')))
def test_parser_price_type_is_projection_of_typed_scope(text,expected_type,expected_scope):
    p=parse_pricing_query(text); assert p.price.type is expected_type; assert p.price_scope.comparison_scope==expected_scope

@pytest.mark.parametrize(('text','unit'),(('Soporte por hora',ChargedUnit.HOUR.value),('Hora adicional',ChargedUnit.HOUR.value),('Servicio por visita',ChargedUnit.VISIT.value),('Precio por equipo',ChargedUnit.UNIT.value),('Precios por equipo',ChargedUnit.UNIT.value),('Abono mensual',ChargedUnit.MONTH.value),('Implementación por proyecto',ChargedUnit.PROJECT.value),('Precio total',ChargedUnit.TOTAL.value)))
def test_offer_extractor_projects_charged_unit_from_typed_scope(text,unit): assert _values(text,'charged_unit')=={unit}

@pytest.mark.parametrize(('text','expected'),(('Desde $30.000',PriceBound.LOWER_BOUND.value),('A partir de $30.000',PriceBound.LOWER_BOUND.value),('Precio mínimo $30.000',PriceBound.MINIMUM.value),('Presupuesto a consultar',PriceBound.QUOTE_REQUIRED.value),('Precio exacto $30.000',PriceBound.EXACT.value)))
def test_offer_extractor_projects_price_bound_from_typed_scope(text,expected): assert _values(text,'price_bound')=={expected}

def test_plain_number_does_not_become_exact_source_bound(): assert _values('Reparación $30.000','price_bound')==set()
def test_quote_required_is_typed_centrally():
    s=normalize_price_scope('Presupuesto a consultar',has_price=False); assert s.price_bound is PriceBoundMeaning.QUOTE_REQUIRED; assert s.status.value=='EXPLICIT'

@pytest.mark.parametrize(('text','expected'),(('Precio por hora','PER_HOUR'),('Abono mensual','PER_MONTH'),('Servicio por visita','PER_VISIT'),('Precio por equipo','PER_UNIT'),('Implementación por proyecto','PER_PROJECT'),('Precio total','FIXED_TOTAL'),('72hs de demora','UNKNOWN'),('mes estimado de demora','UNKNOWN'),('visita técnica incluida','UNKNOWN')))
def test_price_context_uses_same_conservative_scope_engine(text,expected): assert _price_scope(text.casefold())==expected

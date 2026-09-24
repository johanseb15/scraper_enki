import json
from pathlib import Path

from src.aplicacion.parser_consulta_pricing import parse_pricing_query


def test_monitor_condition_does_not_become_pc_condition():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC con monitor nuevo por $500.000"
    )

    assert parsed.condition == "UNKNOWN"


def test_previous_monitor_condition_does_not_become_offered_pc_condition():
    parsed = parse_pricing_query(
        "Tengo un monitor nuevo. Me ofrecieron una PC por $500.000"
    )

    assert parsed.condition == "UNKNOWN"


def test_negated_new_pc_does_not_imply_new_or_used():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC que no es nueva por $500.000"
    )

    assert parsed.condition == "UNKNOWN"


def test_mixed_pc_and_monitor_conditions_have_no_single_bundle_condition():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC usada con monitor nuevo por $500.000"
    )

    assert parsed.condition == "UNKNOWN"


def test_explicit_pc_condition_remains_when_monitor_has_no_condition():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC usada con monitor por $500.000"
    )

    assert parsed.condition == "USED"


def test_context_pc_condition_does_not_become_priced_monitor_condition():
    parsed = parse_pricing_query(
        "Tengo una PC nueva. Me ofrecieron un monitor por $100.000"
    )

    assert parsed.device_type is None
    assert parsed.condition == "UNKNOWN"


def test_unrelated_monitor_condition_does_not_erase_explicit_pc_condition():
    parsed = parse_pricing_query(
        "Tengo un monitor nuevo. Me ofrecieron una PC usada por $500.000"
    )

    assert parsed.condition == "USED"


def test_unrelated_used_monitor_does_not_erase_explicit_new_pc_condition():
    parsed = parse_pricing_query(
        "Tengo un monitor usado. Me ofrecieron una PC nueva por $500.000"
    )

    assert parsed.condition == "NEW"


def test_context_monitor_condition_does_not_conflict_with_pc_bundle_clause():
    parsed = parse_pricing_query(
        "Tengo un monitor nuevo. "
        "Me ofrecieron una PC usada con monitor por $500.000"
    )

    assert parsed.condition == "USED"


def test_mixed_pc_and_monitor_plus_conditions_stay_unknown():
    parsed = parse_pricing_query("PC usada + monitor nuevo")

    assert parsed.condition == "UNKNOWN"


def test_context_pc_condition_does_not_conflict_with_offered_pc_condition():
    parsed = parse_pricing_query(
        "Tengo una PC nueva. Me ofrecieron una PC usada por $500.000"
    )

    assert parsed.condition == "USED"


def test_context_used_pc_does_not_conflict_with_offered_new_pc_condition():
    parsed = parse_pricing_query(
        "Tengo una PC usada. Me ofrecieron una PC nueva por $500.000"
    )

    assert parsed.condition == "NEW"


def test_context_pc_condition_does_not_fill_unqualified_offered_pc():
    parsed = parse_pricing_query(
        "Tengo una PC nueva. Me ofrecieron otra PC por $500.000"
    )

    assert parsed.condition == "UNKNOWN"


def test_conflicting_conditions_inside_same_offer_stay_unknown():
    parsed = parse_pricing_query(
        "Me ofrecieron esta PC usada, pero la anuncian como PC nueva por $500.000"
    )

    assert parsed.condition == "UNKNOWN"


def test_context_notebook_does_not_become_condition_target_for_offered_pc():
    parsed = parse_pricing_query(
        "Tengo una notebook nueva. Me ofrecieron una PC usada por $500.000"
    )

    assert parsed.condition == "USED"


def test_context_pc_does_not_become_condition_target_for_offered_notebook():
    parsed = parse_pricing_query(
        "Tengo una PC usada. Me ofrecieron una notebook nueva por $500.000"
    )

    assert parsed.condition == "NEW"


def test_device_type_and_condition_share_offered_pc_target():
    parsed = parse_pricing_query(
        "Tengo una notebook nueva. Me ofrecieron una PC usada por $500.000"
    )

    assert parsed.device_type == "PC"
    assert parsed.condition == "USED"


def test_device_type_and_condition_share_offered_notebook_target():
    parsed = parse_pricing_query(
        "Tengo una PC usada. Me ofrecieron una notebook nueva por $500.000"
    )

    assert parsed.device_type == "NOTEBOOK"
    assert parsed.condition == "NEW"


def test_context_device_does_not_replace_unqualified_economic_target():
    parsed = parse_pricing_query(
        "Tengo una notebook. Me ofrecieron una PC por $500.000"
    )

    assert parsed.device_type == "PC"
    assert parsed.condition == "UNKNOWN"


def test_two_device_types_in_one_offer_have_no_single_device_target():
    parsed = parse_pricing_query(
        "Me ofrecieron una PC y una notebook por $900.000"
    )

    assert parsed.device_type is None
    assert parsed.condition == "UNKNOWN"


def test_web_real_005_components_do_not_replace_offered_pc_target():
    corpus = Path("data/language/observed_user_raw_v1.jsonl")
    raw_text = next(
        row["raw_text"]
        for line in corpus.read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["metadata"]["legacy_case_id"]
        == "WEB_REAL_005"
    )

    parsed = parse_pricing_query(raw_text)

    assert parsed.device_type == "PC"
    assert parsed.condition == "USED"


def test_device_target_can_appear_after_quoted_amount():
    parsed = parse_pricing_query(
        "Tengo una notebook, me ofrecieron por $500.000 una PC usada"
    )

    assert parsed.device_type == "PC"
    assert parsed.condition == "USED"


def test_unqualified_device_target_can_appear_after_quoted_amount():
    parsed = parse_pricing_query(
        "Tengo una notebook, me ofrecieron por $500.000 una PC"
    )

    assert parsed.device_type == "PC"
    assert parsed.condition == "UNKNOWN"


def test_offer_target_after_amount_and_offer_verb_is_not_context_device():
    parsed = parse_pricing_query(
        "Tengo una notebook, por $500.000 me ofrecieron una PC usada"
    )

    assert parsed.device_type == "PC"
    assert parsed.condition == "USED"


def test_web_real_006_keeps_pc_target_with_unknown_condition():
    corpus = Path("data/language/observed_user_raw_v1.jsonl")
    raw_text = next(
        row["raw_text"]
        for line in corpus.read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["metadata"]["legacy_case_id"]
        == "WEB_REAL_006"
    )

    parsed = parse_pricing_query(raw_text)

    assert parsed.device_type == "PC"
    assert parsed.condition == "UNKNOWN"


def test_context_pc_before_comma_does_not_become_unsupported_monitor_target():
    parsed = parse_pricing_query(
        "Tengo una PC nueva, me ofrecieron un monitor por $100.000"
    )

    assert parsed.device_type is None
    assert parsed.condition == "UNKNOWN"


def test_context_notebook_before_comma_does_not_replace_offered_pc():
    parsed = parse_pricing_query(
        "Tengo una notebook nueva, me ofrecieron una PC usada por $500.000"
    )

    assert parsed.device_type == "PC"
    assert parsed.condition == "USED"

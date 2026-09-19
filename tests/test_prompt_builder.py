from app.services.prompt_builder import build_sql_prompt


def test_prompt_contains_schema_question_and_safety_rules(demo_schema):
    prompt = build_sql_prompt("Show customers in Bihar", demo_schema, max_rows=25)
    assert "customers(" in prompt
    assert "orders(" in prompt
    assert "Show customers in Bihar" in prompt
    assert "Read data only" in prompt
    assert "25 rows" in prompt

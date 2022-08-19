from pathlib import Path
from textwrap import dedent
import pytest

from attack_flow.docs import (
    generate_example_flows,
    generate_schema_docs,
    human_name,
    insert_docs,
    make_target,
    RefType,
    Schema,
    SchemaProperty,
)


def test_schema_property_string():
    sp = SchemaProperty(
        "test-prop",
        False,
        {
            "description": "My description",
            "type": "string",
        },
    )
    assert sp.name == "test-prop"
    assert sp.type == "string"
    assert not sp.required
    assert sp.type_markup == "``string``"


def test_schema_property_requires_description():
    with pytest.raises(ValueError):
        SchemaProperty(
            "test-prop",
            False,
            {
                "type": "string",
            },
        )


def test_schema_property_uuid():
    sp = SchemaProperty(
        "test-uuid",
        True,
        {
            "description": "My description",
            "type": "string",
            "format": "uuid",
        },
    )
    assert sp.name == "test-uuid"
    assert sp.type == "string"
    assert sp.required
    assert sp.type_markup == "``uuid``"


def test_schema_property_datetime():
    sp = SchemaProperty(
        "test-datetime",
        True,
        {
            "description": "My description",
            "type": "string",
            "format": "date-time",
        },
    )
    assert sp.name == "test-datetime"
    assert sp.type == "string"
    assert sp.required
    assert sp.type_markup == "``date-time``"


def test_schema_property_array_of_string():
    sp = SchemaProperty(
        "test-array",
        True,
        {"description": "My description", "type": "array", "items": {"type": "string"}},
    )
    assert sp.name == "test-array"
    assert sp.type == "array"
    assert sp.subtype == "string"
    assert sp.required
    assert sp.type_markup == "``list`` of ``string``"


def test_schema_property_array_of_object():
    """Array of objects is not allowed."""
    with pytest.raises(ValueError):
        sp = SchemaProperty(
            "test-array2",
            True,
            {
                "description": "My description",
                "type": "array",
                "items": {"type": "object"},
            },
        )


def test_schema_property_object():
    sp = SchemaProperty(
        "test-object",
        True,
        {
            "description": "My description",
            "type": "object",
            "properties": {"foo": "string"},
        },
    )
    assert sp.name == "test-object"
    assert sp.type == "object"
    assert sp.subtype is None
    assert sp.required
    assert sp.type_markup == ":ref:`schema_test_object`"


def test_schema_property_enum():
    sp = SchemaProperty(
        "test-enum",
        True,
        {"description": "My description", "type": "string", "enum": ["foo", "bar"]},
    )
    assert sp.name == "test-enum"
    assert sp.type == "string"
    assert sp.required
    assert sp.type_markup == '``string`` Allowed values: "foo", "bar"'


def test_schema_property_ref():
    sp = SchemaProperty(
        "test-ref",
        True,
        {
            "description": "My identity ref",
            "$ref": "./identifier.json",
            "x-referenceType": ["identity"],
        },
    )
    assert sp.name == "test-ref"
    assert isinstance(sp.type, RefType)
    assert sp.required
    assert sp.type_markup == "``identifier`` (of type ``identity``)"


def test_schema_property_untyped_ref():
    sp = SchemaProperty(
        "test-ref",
        True,
        {
            "description": "My generic ref",
            "$ref": "./identifier.json",
        },
    )
    assert sp.name == "test-ref"
    assert isinstance(sp.type, RefType)
    assert sp.required
    assert sp.type_markup == "``identifier``"


def test_schema_property_list_of_ref():
    sp = SchemaProperty(
        "test-ref-list",
        True,
        {
            "description": "My generic ref",
            "type": "array",
            "items": {
                "$ref": "./identifier.json",
            },
        },
    )
    assert sp.name == "test-ref-list"
    assert sp.type == "array"
    assert sp.required
    assert sp.type_markup == "``list`` of ``identifier``"


def test_schema():
    schema = Schema(
        "my-object",
        {
            "type": "object",
            "description": "My Schema",
            "properties": {
                "name": {"description": "My name", "type": "string"},
                "hobbies": {
                    "description": "My hobbies",
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    )
    assert schema.name == "my-object"
    assert schema.description == "My Schema"
    assert schema.properties["name"].type == "string"
    assert schema.properties["hobbies"].type == "array"
    assert schema.properties["hobbies"].subtype == "string"


def test_generate_schema_docs():
    schema = Schema(
        "my-object",
        {
            "type": "object",
            "description": "My Schema",
            "properties": {
                "name": {"description": "My name", "type": "string"},
                "hobbies": {
                    "description": "My hobbies",
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "x-exampleObject": "my-object--6b44da40-c357-4eed-83b6-5b183c6de006",
        },
    )
    examples = {"my-object--6b44da40-c357-4eed-83b6-5b183c6de006": {"foo": "bar"}}
    actual_markup = generate_schema_docs(schema, examples)
    expected_markup = [
        ".. _schema_my_object:",
        "",
        "My Object",
        "~~~~~~~~~",
        "",
        "My Schema",
        "",
        ".. list-table::",
        "   :widths: 20 30 50",
        "   :header-rows: 1",
        "",
        "   * - Property Name",
        "     - Type",
        "     - Description",
        "   * - **type**",
        "     - ``string``",
        "     - The value of this property **must** be ``my-object``.",
        "   * - **name** *(optional)*",
        "     - ``string``",
        "     - My name",
        "   * - **hobbies** *(optional)*",
        "     - ``list`` of ``string``",
        "     - My hobbies",
        "",
        "*Example:*",
        "",
        ".. code:: json",
        "",
        "    {",
        '      "foo": "bar"',
        "    }",
        "",
    ]

    assert actual_markup == expected_markup


def test_make_target():
    assert make_target("? ASDF; 123 ") == ".. _schema_asdf_123:"


def test_insert_docs():
    old_doc = iter(
        [
            "old text 1",
            "old text 2",
            ".. JSON_SCHEMA",
            "old html 1",
            "old html 2",
            ".. /JSON_SCHEMA",
            "old text 3",
            "old text 4",
        ]
    )

    html = [
        "new html 1",
        "new html 2",
    ]

    actual = iter(insert_docs(old_doc, html, "JSON_SCHEMA").splitlines())
    assert next(actual) == "old text 1"
    assert next(actual) == "old text 2"
    assert next(actual).startswith(".. JSON_SCHEMA")
    assert next(actual) == ""
    assert next(actual) == "new html 1"
    assert next(actual) == "new html 2"
    assert next(actual) == ".. /JSON_SCHEMA"
    assert next(actual) == "old text 3"
    assert next(actual) == "old text 4"


def test_insert_docs_no_start_tag():
    old_doc = iter(
        [
            "old text 1",
            "old text 2",
            "old text 3",
            "old text 4",
        ]
    )

    with pytest.raises(RuntimeError):
        insert_docs(old_doc, [], tag="JSON_SCHEMA")


def test_insert_docs_no_end_tag():
    old_doc = iter(
        [
            "old text 1",
            "old text 2",
            ".. JSON_SCHEMA",
            "old text 3",
            "old text 4",
        ]
    )

    with pytest.raises(RuntimeError):
        insert_docs(old_doc, [], tag="JSON_SCHEMA")


def test_human_name():
    assert human_name("foo") == "Foo"
    assert human_name("foo-bar") == "Foo Bar"


def test_generate_example_flows():
    jsons = [Path("tests/fixtures/flow1.json"), Path("tests/fixtures/flow2.json")]
    afds = [Path("tests/fixtures/flow1.afd")]
    result = generate_example_flows(jsons, afds)
    assert result == [
        ".. list-table::",
        "  :widths: 25 25 50",
        "  :header-rows: 1",
        "",
        "  * - Report",
        "    - Authors",
        "    - Description",
        "  * - **Test Fixture 1**",
        "",
        "      .. raw:: html",
        "",
        '        <p><a href="../corpus/flow1.json"><i class="fa fa-file-text"></i>JSON</a></p>',
        '        <p><a href="../corpus/flow1.dot"><i class="fa fa-snowflake-o"></i>Graphviz</a></p>',
        '        <p><a href="../corpus/flow1.dot.png"><i class="fa fa-picture-o"></i>Image</a></p>',
        '        <p><a target="_blank" href="/builder/?load=%2fcorpus%2fflow1.afd"><i class="fa fa-wrench"></i>Attack Flow Builder</a> (TODO)</p>',
        "",
        "    - Center for Threat-Informed Defense",
        "    - TODO: fix description field in AF2.",
        "  * - **Test Fixture 2**",
        "",
        "      .. raw:: html",
        "",
        '        <p><a href="../corpus/flow2.json"><i class="fa fa-file-text"></i>JSON</a></p>',
        '        <p><a href="../corpus/flow2.dot"><i class="fa fa-snowflake-o"></i>Graphviz</a></p>',
        '        <p><a href="../corpus/flow2.dot.png"><i class="fa fa-picture-o"></i>Image</a></p>',
        "",
        "    - Center for Threat-Informed Defense",
        "    - TODO: fix description field in AF2.",
        "",
    ]
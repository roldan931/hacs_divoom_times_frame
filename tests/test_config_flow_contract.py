"""Check Home Assistant's config flow discovery contract."""

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "divoom_times_frame"


class ConfigFlowContractTests(unittest.TestCase):
    """Verify that Home Assistant can discover the declared flow class."""

    def test_manifest_config_flow_has_discoverable_class(self) -> None:
        manifest = json.loads((INTEGRATION / "manifest.json").read_text("utf-8"))
        self.assertTrue(manifest["config_flow"])

        module = ast.parse((INTEGRATION / "config_flow.py").read_text("utf-8"))
        classes = {
            node.name: node
            for node in module.body
            if isinstance(node, ast.ClassDef)
        }
        self.assertIn("ConfigFlow", classes)
        self.assertTrue(
            any(
                isinstance(base, ast.Attribute) and base.attr == "ConfigFlow"
                for base in classes["ConfigFlow"].bases
            )
        )

    def test_form_schema_uses_serializable_primitive_fields(self) -> None:
        module = ast.parse((INTEGRATION / "config_flow.py").read_text("utf-8"))
        schema_assignment = next(
            node
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "STEP_USER_SCHEMA"
                for target in node.targets
            )
        )
        schema_call = schema_assignment.value
        self.assertIsInstance(schema_call, ast.Call)
        self.assertIsInstance(schema_call.func, ast.Attribute)
        self.assertEqual(schema_call.func.attr, "Schema")

        fields = schema_call.args[0]
        self.assertIsInstance(fields, ast.Dict)
        self.assertEqual(
            [ast.unparse(value) for value in fields.values],
            ["str", "str", "int"],
        )
        self.assertTrue(
            all(
                isinstance(value, ast.Name)
                for value in fields.values
            )
        )

    def test_form_validation_errors_have_translations(self) -> None:
        expected_errors = {
            "invalid_ip",
            "invalid_device_id",
            "invalid_port",
        }
        for translation in ("en", "es"):
            with self.subTest(translation=translation):
                strings = json.loads(
                    (
                        INTEGRATION
                        / "translations"
                        / f"{translation}.json"
                    ).read_text("utf-8")
                )
                self.assertTrue(
                    expected_errors.issubset(strings["config"]["error"])
                )


if __name__ == "__main__":
    unittest.main()

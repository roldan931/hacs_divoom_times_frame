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


if __name__ == "__main__":
    unittest.main()

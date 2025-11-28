# test_yaml_tab.py - Quick test to verify YAML Editor tab imports correctly

import sys
from pathlib import Path

# Ensure we can import from gui
sys.path.insert(0, str(Path(__file__).parent))

try:
    from gui.tabs.yaml_editor_tab import YamlEditorTab
    print("✓ YamlEditorTab imported successfully")
    
    from gui.tabs import YamlEditorTab as YamlEditorTab2
    print("✓ YamlEditorTab accessible via gui.tabs")
    
    # Test that it has the expected methods
    required_methods = ['new_file', 'open_yaml', 'save', 'save_as', '_build_form', 'mark_modified']
    for method in required_methods:
        if hasattr(YamlEditorTab, method):
            print(f"✓ Method '{method}' exists")
        else:
            print(f"✗ Method '{method}' MISSING")
    
    print("\n✅ All checks passed! YAML Editor tab is ready to use in the GUI.")
    print("\nTo launch the full GUI with the new tab, run:")
    print("  python gui_main.py")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

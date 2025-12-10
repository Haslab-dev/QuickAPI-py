"""
Test script for simplified QuickAPI implementation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_template_engine():
    """Test simplified template engine"""
    print("Testing template engine...")
    
    from quickapi.templates import Template, html, TemplateResponse
    
    # Test HTML builder
    div = html.div("Hello World", class_="test")
    assert "div" in str(div)
    assert "Hello World" in str(div)
    print("✓ HTML builder works")
    
    # Test template response
    response = TemplateResponse(
        template_string="<h1>{title}</h1>",
        context={"title": "Test"},
        title="Test Page"
    )
    assert "Test Page" in response.content.decode("utf-8")
    print("✓ Template response works")
    
    # Test layout
    from quickapi.templates import default_layout
    layout = default_layout("Test")
    wrapped = layout.wrap("<p>Content</p>")
    assert "Test" in wrapped
    assert "Content" in wrapped
    print("✓ Layout works")


def test_ui_components():
    """Test simplified UI components"""
    print("Testing UI components...")
    
    from quickapi.ui import Textbox, Slider, Button, Text
    
    # Test textbox
    textbox = Textbox(label="Test", value="Hello")
    input_html = textbox.render_input()
    assert "Test" in input_html
    assert "Hello" in input_html
    print("✓ Textbox component works")
    
    # Test slider
    slider = Slider(label="Test", value=50, minimum=0, maximum=100)
    input_html = slider.render_input()
    assert "Test" in input_html
    assert "50" in input_html
    print("✓ Slider component works")
    
    # Test button
    button = Button(value="Test", variant="primary")
    input_html = button.render_input()
    assert "Test" in input_html
    assert "bg-blue-600" in input_html  # primary variant creates blue background
    print("✓ Button component works")
    
    # Test text output
    text = Text(label="Test", value="Result")
    output_html = text.render_output()
    assert "Test" in output_html
    assert "Result" in output_html
    print("✓ Text component works")


def test_ui():
    """Test UI class"""
    print("Testing UI...")
    
    from quickapi.ui import UI, Textbox, Text
    
    # Test UI creation
    def test_fn(text):
        return f"Processed: {text}"
    
    ui = UI(
        fn=test_fn,
        inputs=Textbox(label="Input"),
        outputs=Text(label="Output"),
        title="Test UI"
    )
    
    assert ui.title == "Test UI"
    assert len(ui.inputs) == 1
    assert len(ui.outputs) == 1
    assert ui.api_name == "test_fn"
    print("✓ UI creation works")
    
    # Test template rendering
    template = ui._render_template()
    assert "Test UI" in template
    assert "Input" in template
    assert "Output" in template
    print("✓ UI template rendering works")
    
    # Test JavaScript generation
    js = ui._get_javascript()
    assert "submitForm" in js
    assert "input_0" in js
    assert "output_0" in js
    print("✓ UI JavaScript generation works")


def main():
    """Run all tests"""
    print("Running simplified QuickAPI tests...")
    print("=" * 50)
    
    try:
        test_template_engine()
        print()
        test_ui_components()
        print()
        test_ui()
        print()
        print("=" * 50)
        print("✅ All tests passed!")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
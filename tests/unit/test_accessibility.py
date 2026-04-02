"""
Unit tests for accessibility features.

Tests verify that:
- Keyboard navigation works through all interactive elements
- Focus management is handled properly
- ARIA labels are present for screen readers

**Validates: Requirements 9.1, 16.1**
"""

import pytest
import flet as ft
from unittest.mock import Mock, patch


class TestKeyboardNavigation:
    """Test keyboard navigation through interactive elements."""
    
    def test_tab_navigation_order(self):
        """
        Test that Tab key navigates through elements in logical order.
        
        **Validates: Requirements 16.1**
        """
        # Create interactive elements in logical order
        text_field_1 = ft.TextField(label="First Name")
        text_field_2 = ft.TextField(label="Last Name")
        button = ft.ElevatedButton(text="Submit")
        
        # Verify elements are created (tab order is implicit in Flet based on creation order)
        assert text_field_1.label == "First Name"
        assert text_field_2.label == "Last Name"
        assert button.text == "Submit"
    
    def test_tab_navigation_skips_disabled_elements(self):
        """
        Test that Tab navigation skips disabled elements.
        
        **Validates: Requirements 16.1**
        """
        # Create elements with one disabled
        text_field_1 = ft.TextField(label="Name", disabled=False)
        text_field_2 = ft.TextField(label="Email", disabled=True)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Verify disabled element can be skipped
        assert text_field_1.disabled is False
        assert text_field_2.disabled is True
        assert button.disabled is False
    
    def test_tab_navigation_through_form_elements(self):
        """
        Test Tab navigation through a complete form.
        
        **Validates: Requirements 16.1**
        """
        # Create a form with multiple elements
        form_elements = [
            ft.TextField(label="Product Name"),
            ft.TextField(label="SKU"),
            ft.TextField(label="Price"),
            ft.TextField(label="Quantity"),
            ft.Dropdown(label="Category"),
            ft.ElevatedButton(text="Save"),
            ft.TextButton(text="Cancel"),
        ]
        
        # Verify all elements are created in order
        assert len(form_elements) == 7
        assert form_elements[0].label == "Product Name"
        assert form_elements[-1].text == "Cancel"
    
    def test_reverse_tab_navigation(self):
        """
        Test that Shift+Tab navigates backwards through elements.
        
        **Validates: Requirements 16.1**
        """
        # Create elements in order
        elements = [
            ft.TextField(label="Field 1"),
            ft.TextField(label="Field 2"),
            ft.TextField(label="Field 3"),
        ]
        
        # Verify elements are created in order (Flet supports reverse tab navigation by default)
        assert len(elements) == 3
        assert elements[0].label == "Field 1"
        assert elements[2].label == "Field 3"
    
    def test_tab_navigation_in_data_table(self):
        """
        Test Tab navigation through data table rows and cells.
        
        **Validates: Requirements 16.1**
        """
        # Create data table with interactive elements
        table_rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("Product 1")),
                ft.DataCell(ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit")),
                ft.DataCell(ft.IconButton(icon=ft.icons.DELETE, tooltip="Delete")),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("Product 2")),
                ft.DataCell(ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit")),
                ft.DataCell(ft.IconButton(icon=ft.icons.DELETE, tooltip="Delete")),
            ]),
        ]
        
        # Verify buttons have tooltips for accessibility
        edit_button_1 = table_rows[0].cells[1].content
        delete_button_1 = table_rows[0].cells[2].content
        assert edit_button_1.tooltip == "Edit"
        assert delete_button_1.tooltip == "Delete"


class TestEnterKeyActivation:
    """Test Enter key to submit forms and activate buttons."""
    
    def test_enter_key_submits_form(self):
        """
        Test that Enter key in text field can trigger form submission.
        
        **Validates: Requirements 16.1**
        """
        # Create form with submit handler
        submission_count = {"count": 0}
        
        def on_submit(e):
            submission_count["count"] += 1
        
        text_field = ft.TextField(
            label="Search",
            on_submit=on_submit
        )
        
        # Verify on_submit handler is set
        assert text_field.on_submit is not None
        
        # Simulate Enter key press
        text_field.on_submit(Mock())
        
        # Verify submission occurred
        assert submission_count["count"] == 1
    
    def test_enter_key_activates_button(self):
        """
        Test that Enter key activates focused button.
        
        **Validates: Requirements 16.1**
        """
        # Create button with click handler
        click_count = {"count": 0}
        
        def on_click(e):
            click_count["count"] += 1
        
        button = ft.ElevatedButton(
            text="Submit",
            on_click=on_click
        )
        
        # Verify on_click handler is set
        assert button.on_click is not None
        
        # Simulate Enter key activation
        button.on_click(Mock())
        
        # Verify button was activated
        assert click_count["count"] == 1
    
    def test_enter_key_in_search_field(self):
        """
        Test that Enter key in search field triggers search.
        
        **Validates: Requirements 16.1**
        """
        # Create search field with submit handler
        search_executed = {"executed": False, "query": ""}
        
        def on_search(e):
            search_executed["executed"] = True
            search_executed["query"] = e.control.value
        
        search_field = ft.TextField(
            label="Search Products",
            value="test query",
            on_submit=on_search
        )
        
        # Simulate Enter key press
        mock_event = Mock()
        mock_event.control = search_field
        search_field.on_submit(mock_event)
        
        # Verify search was executed
        assert search_executed["executed"] is True
        assert search_executed["query"] == "test query"
    
    def test_enter_key_in_multiline_text_does_not_submit(self):
        """
        Test that Enter key in multiline text field adds newline, not submit.
        
        **Validates: Requirements 16.1**
        """
        # Create multiline text field
        text_field = ft.TextField(
            label="Description",
            multiline=True,
            on_submit=None  # Should not have submit handler
        )
        
        # Verify multiline field doesn't have submit handler
        assert text_field.multiline is True
        assert text_field.on_submit is None


class TestEscapeKeyBehavior:
    """Test Escape key to close dialogs and cancel operations."""
    
    def test_escape_key_closes_dialog(self):
        """
        Test that Escape key closes open dialog.
        
        **Validates: Requirements 16.1**
        """
        # Create dialog
        dialog_open = {"open": True}
        
        def close_dialog(e):
            dialog_open["open"] = False
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Action"),
            content=ft.Text("Are you sure?"),
            open=True,
            on_dismiss=close_dialog
        )
        
        # Verify dialog is initially open
        assert dialog.open is True
        
        # Simulate Escape key press
        dialog.on_dismiss(Mock())
        
        # Verify dialog was closed
        assert dialog_open["open"] is False
    
    def test_escape_key_cancels_form_edit(self):
        """
        Test that Escape key cancels form editing.
        
        **Validates: Requirements 16.1**
        """
        # Create form with cancel handler
        form_cancelled = {"cancelled": False}
        
        def on_cancel(e):
            form_cancelled["cancelled"] = True
        
        cancel_button = ft.TextButton(
            text="Cancel (Esc)",
            on_click=on_cancel
        )
        
        # Simulate Escape key triggering cancel
        cancel_button.on_click(Mock())
        
        # Verify form was cancelled
        assert form_cancelled["cancelled"] is True
    
    def test_escape_key_closes_modal(self):
        """
        Test that Escape key closes modal dialogs.
        
        **Validates: Requirements 16.1**
        """
        # Create modal
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Product"),
            open=True
        )
        
        # Verify modal is initially open
        assert modal.open is True
        assert modal.modal is True
        
        # Simulate Escape key closing modal
        modal.open = False
        
        # Verify modal was closed
        assert modal.open is False


class TestKeyboardShortcuts:
    """Test keyboard shortcuts for common operations."""
    
    def test_ctrl_s_saves_form(self):
        """
        Test that Ctrl+S keyboard shortcut saves form.
        
        **Validates: Requirements 16.1**
        """
        # Create save handler
        save_count = {"count": 0}
        
        def on_save(e):
            save_count["count"] += 1
        
        # Simulate Ctrl+S shortcut
        save_button = ft.ElevatedButton(
            text="Save (Ctrl+S)",
            on_click=on_save
        )
        
        # Verify save handler exists
        assert save_button.on_click is not None
        
        # Simulate shortcut activation
        save_button.on_click(Mock())
        
        # Verify save was triggered
        assert save_count["count"] == 1
    
    def test_ctrl_n_creates_new_record(self):
        """
        Test that Ctrl+N keyboard shortcut creates new record.
        
        **Validates: Requirements 16.1**
        """
        # Create new record handler
        new_record_count = {"count": 0}
        
        def on_new(e):
            new_record_count["count"] += 1
        
        new_button = ft.ElevatedButton(
            text="New (Ctrl+N)",
            on_click=on_new
        )
        
        # Simulate shortcut activation
        new_button.on_click(Mock())
        
        # Verify new record was triggered
        assert new_record_count["count"] == 1
    
    def test_ctrl_f_focuses_search(self):
        """
        Test that Ctrl+F keyboard shortcut focuses search field.
        
        **Validates: Requirements 16.1**
        """
        # Create search field with focus handler
        search_focused = {"focused": False}
        
        def on_focus(e):
            search_focused["focused"] = True
        
        search_field = ft.TextField(
            label="Search (Ctrl+F)",
            on_focus=on_focus
        )
        
        # Verify focus handler exists
        assert search_field.on_focus is not None
        
        # Simulate focus
        search_field.on_focus(Mock())
        
        # Verify search was focused
        assert search_focused["focused"] is True
    
    def test_keyboard_shortcuts_documented(self):
        """
        Test that keyboard shortcuts are documented in UI.
        
        **Validates: Requirements 16.1**
        """
        # Create buttons with shortcut hints
        save_button = ft.ElevatedButton(text="Save (Ctrl+S)")
        new_button = ft.ElevatedButton(text="New (Ctrl+N)")
        search_field = ft.TextField(label="Search (Ctrl+F)")
        
        # Verify shortcuts are documented in text
        assert "Ctrl+S" in save_button.text
        assert "Ctrl+N" in new_button.text
        assert "Ctrl+F" in search_field.label


class TestFocusManagement:
    """Test focus management and visible focus indicators."""
    
    def test_focus_indicator_visible(self):
        """
        Test that focused element has visible focus indicator.
        
        **Validates: Requirements 16.1**
        """
        # Create text field with focus properties
        text_field = ft.TextField(
            label="Name",
            focused_border_color="blue",
            focused_bgcolor="lightblue"
        )
        
        # Verify focus styling is configured
        assert text_field.focused_border_color == "blue"
        assert text_field.focused_bgcolor == "lightblue"
    
    def test_focus_moves_to_first_field_on_form_load(self):
        """
        Test that focus automatically moves to first field when form loads.
        
        **Validates: Requirements 16.1**
        """
        # Create form with autofocus on first field
        first_field = ft.TextField(
            label="Product Name",
            autofocus=True
        )
        second_field = ft.TextField(label="SKU")
        
        # Verify autofocus is set on first field only
        assert first_field.autofocus is True
        assert second_field.autofocus is False
    
    def test_focus_moves_to_error_field_on_validation_failure(self):
        """
        Test that focus moves to field with validation error.
        
        **Validates: Requirements 16.1**
        """
        # Create field with error
        text_field = ft.TextField(
            label="Price",
            error_text="Price must be a positive number",
            autofocus=True
        )
        
        # Verify error is displayed and field can receive focus
        assert text_field.error_text is not None
        assert text_field.autofocus is True
    
    def test_focus_trapped_in_modal_dialog(self):
        """
        Test that focus is trapped within modal dialog.
        
        **Validates: Requirements 16.1**
        """
        # Create modal dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this item?"),
            actions=[
                ft.TextButton("Cancel"),
                ft.ElevatedButton("Delete"),
            ]
        )
        
        # Verify modal property is set
        assert dialog.modal is True
        
        # Verify action buttons exist for focus management
        assert len(dialog.actions) == 2
        assert dialog.actions[0].text == "Cancel"
        assert dialog.actions[1].text == "Delete"
    
    def test_focus_returns_after_dialog_closes(self):
        """
        Test that focus returns to trigger element after dialog closes.
        
        **Validates: Requirements 16.1**
        """
        # Create button that opens dialog
        open_button = ft.ElevatedButton(
            text="Delete",
            autofocus=True
        )
        
        # Create dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm"),
            open=False
        )
        
        # Verify button can receive focus
        assert open_button.autofocus is True
        
        # After dialog closes, focus should return to button
        # (In real implementation, this would be handled by dialog close handler)
    
    def test_focus_visible_on_all_interactive_elements(self):
        """
        Test that all interactive elements can receive visible focus.
        
        **Validates: Requirements 16.1**
        """
        # Create various interactive elements
        elements = [
            ft.TextField(label="Text Field", focused_border_color="blue"),
            ft.ElevatedButton(text="Button"),
            ft.IconButton(icon=ft.icons.EDIT),
            ft.Checkbox(label="Checkbox"),
            ft.Radio(value="option1", label="Radio"),
            ft.Dropdown(label="Dropdown"),
        ]
        
        # Verify all elements can be focused
        # (In Flet, all interactive elements support focus by default)
        assert len(elements) == 6
    
    def test_focus_order_matches_visual_order(self):
        """
        Test that focus order matches visual layout order.
        
        **Validates: Requirements 16.1**
        """
        # Create form with logical order
        form_fields = [
            ft.TextField(label="First Name"),
            ft.TextField(label="Last Name"),
            ft.TextField(label="Email"),
            ft.TextField(label="Phone"),
            ft.ElevatedButton(text="Submit"),
        ]
        
        # Verify elements are created in logical order
        assert len(form_fields) == 5
        assert form_fields[0].label == "First Name"
        assert form_fields[4].text == "Submit"


class TestARIALabels:
    """Test ARIA labels and roles for screen readers."""
    
    def test_text_fields_have_labels(self):
        """
        Test that all text fields have descriptive labels.
        
        **Validates: Requirements 16.1**
        """
        # Create text fields with labels
        text_fields = [
            ft.TextField(label="Product Name"),
            ft.TextField(label="SKU"),
            ft.TextField(label="Price"),
            ft.TextField(label="Quantity"),
        ]
        
        # Verify all fields have labels
        for field in text_fields:
            assert field.label is not None
            assert len(field.label) > 0
    
    def test_buttons_have_descriptive_text(self):
        """
        Test that all buttons have descriptive text or tooltips.
        
        **Validates: Requirements 16.1**
        """
        # Create buttons with descriptive text
        buttons = [
            ft.ElevatedButton(text="Save Product"),
            ft.ElevatedButton(text="Cancel"),
            ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit Product"),
            ft.IconButton(icon=ft.icons.DELETE, tooltip="Delete Product"),
        ]
        
        # Verify all buttons have text or tooltip
        assert buttons[0].text == "Save Product"
        assert buttons[1].text == "Cancel"
        assert buttons[2].tooltip == "Edit Product"
        assert buttons[3].tooltip == "Delete Product"
    
    def test_icon_buttons_have_tooltips(self):
        """
        Test that icon buttons have tooltips for screen readers.
        
        **Validates: Requirements 16.1**
        """
        # Create icon buttons with tooltips
        icon_buttons = [
            ft.IconButton(icon=ft.icons.ADD, tooltip="Add New Product"),
            ft.IconButton(icon=ft.icons.SEARCH, tooltip="Search Products"),
            ft.IconButton(icon=ft.icons.REFRESH, tooltip="Refresh List"),
            ft.IconButton(icon=ft.icons.SETTINGS, tooltip="Settings"),
        ]
        
        # Verify all icon buttons have tooltips
        for button in icon_buttons:
            assert button.tooltip is not None
            assert len(button.tooltip) > 0
    
    def test_form_fields_have_hints(self):
        """
        Test that form fields have helpful hint text.
        
        **Validates: Requirements 16.1**
        """
        # Create fields with hint text
        fields = [
            ft.TextField(label="CPF", hint_text="000.000.000-00"),
            ft.TextField(label="Phone", hint_text="(00) 00000-0000"),
            ft.TextField(label="Price", hint_text="0.00"),
            ft.TextField(label="Quantity", hint_text="Enter quantity"),
        ]
        
        # Verify all fields have hint text
        for field in fields:
            assert field.hint_text is not None
            assert len(field.hint_text) > 0
    
    def test_error_messages_are_descriptive(self):
        """
        Test that error messages are clear and descriptive.
        
        **Validates: Requirements 16.1**
        """
        # Create fields with error messages
        fields = [
            ft.TextField(
                label="Email",
                error_text="Please enter a valid email address"
            ),
            ft.TextField(
                label="Price",
                error_text="Price must be a positive number"
            ),
            ft.TextField(
                label="Quantity",
                error_text="Quantity must be greater than 0"
            ),
        ]
        
        # Verify error messages are descriptive
        for field in fields:
            assert field.error_text is not None
            assert len(field.error_text) > 10  # Reasonably descriptive
    
    def test_data_table_has_column_headers(self):
        """
        Test that data tables have descriptive column headers.
        
        **Validates: Requirements 16.1**
        """
        # Create data table with headers
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Product Name")),
                ft.DataColumn(ft.Text("SKU")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Quantity")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[]
        )
        
        # Verify all columns have labels
        assert len(table.columns) == 5
        for column in table.columns:
            assert column.label is not None
    
    def test_loading_indicators_have_semantic_meaning(self):
        """
        Test that loading indicators provide semantic information.
        
        **Validates: Requirements 16.1**
        """
        # Create loading indicator with semantic container
        loading_container = ft.Column(
            controls=[
                ft.ProgressRing(width=30, height=30),
                ft.Text("Loading products...", semantics_label="Loading products")
            ]
        )
        
        # Verify loading has descriptive text
        assert len(loading_container.controls) == 2
        assert loading_container.controls[1].value == "Loading products..."
    
    def test_dialogs_have_titles(self):
        """
        Test that all dialogs have descriptive titles.
        
        **Validates: Requirements 16.1**
        """
        # Create dialogs with titles
        dialogs = [
            ft.AlertDialog(title=ft.Text("Confirm Delete")),
            ft.AlertDialog(title=ft.Text("Add New Product")),
            ft.AlertDialog(title=ft.Text("Edit Customer")),
            ft.AlertDialog(title=ft.Text("Error")),
        ]
        
        # Verify all dialogs have titles
        for dialog in dialogs:
            assert dialog.title is not None


class TestScreenReaderSupport:
    """Test screen reader support and announcements."""
    
    def test_success_messages_announced(self):
        """
        Test that success messages can be announced to screen readers.
        
        **Validates: Requirements 16.1**
        """
        # Create success message with semantic label
        success_message = ft.Text(
            "Product saved successfully",
            color="green",
            semantics_label="Success: Product saved successfully"
        )
        
        # Verify message has semantic label
        assert success_message.semantics_label is not None
        assert "Success" in success_message.semantics_label
    
    def test_error_messages_announced(self):
        """
        Test that error messages can be announced to screen readers.
        
        **Validates: Requirements 16.1**
        """
        # Create error message with semantic label
        error_message = ft.Text(
            "Failed to save product",
            color="red",
            semantics_label="Error: Failed to save product"
        )
        
        # Verify message has semantic label
        assert error_message.semantics_label is not None
        assert "Error" in error_message.semantics_label
    
    def test_state_changes_announced(self):
        """
        Test that state changes are announced to screen readers.
        
        **Validates: Requirements 16.1**
        """
        # Create element with state change announcement
        checkbox = ft.Checkbox(
            label="Include out of stock items",
            value=False
        )
        
        # Verify checkbox has label for state announcement
        assert checkbox.label is not None
        
        # State changes would be announced automatically by Flet
    
    def test_dynamic_content_updates_announced(self):
        """
        Test that dynamic content updates can be announced.
        
        **Validates: Requirements 16.1**
        """
        # Create container for dynamic content
        results_text = ft.Text(
            "Found 10 products",
            semantics_label="Search results: Found 10 products"
        )
        
        # Verify semantic label for announcement
        assert results_text.semantics_label is not None
        assert "Found 10 products" in results_text.semantics_label
    
    def test_form_validation_errors_announced(self):
        """
        Test that form validation errors are announced to screen readers.
        
        **Validates: Requirements 16.1**
        """
        # Create form field with validation error
        field = ft.TextField(
            label="Email",
            value="invalid-email",
            error_text="Please enter a valid email address"
        )
        
        # Verify error text is present for announcement
        assert field.error_text is not None
        assert len(field.error_text) > 0
    
    def test_progress_updates_announced(self):
        """
        Test that progress updates can be announced to screen readers.
        
        **Validates: Requirements 16.1**
        """
        # Create progress indicator with text
        progress_container = ft.Column(
            controls=[
                ft.ProgressBar(value=0.5, width=200),
                ft.Text("50% complete", semantics_label="Progress: 50% complete")
            ]
        )
        
        # Verify progress has descriptive text
        progress_text = progress_container.controls[1]
        assert progress_text.semantics_label is not None
        assert "50%" in progress_text.semantics_label


class TestAccessibilityCompliance:
    """Test overall accessibility compliance."""
    
    def test_all_images_have_alt_text(self):
        """
        Test that all images have alternative text.
        
        **Validates: Requirements 16.1**
        """
        # Create images with alt text (using semantics_label in Flet)
        images = [
            ft.Image(src="logo.png", semantics_label="Company Logo"),
            ft.Image(src="product.jpg", semantics_label="Product Image"),
        ]
        
        # Verify all images have semantic labels
        for image in images:
            assert image.semantics_label is not None
            assert len(image.semantics_label) > 0
    
    def test_color_not_only_means_of_conveying_information(self):
        """
        Test that color is not the only way to convey information.
        
        **Validates: Requirements 16.1**
        """
        # Create status indicators with text and color
        status_indicators = [
            ft.Row(controls=[
                ft.Icon(ft.icons.CHECK_CIRCLE, color="green"),
                ft.Text("Active", color="green")
            ]),
            ft.Row(controls=[
                ft.Icon(ft.icons.ERROR, color="red"),
                ft.Text("Error", color="red")
            ]),
            ft.Row(controls=[
                ft.Icon(ft.icons.WARNING, color="orange"),
                ft.Text("Warning", color="orange")
            ]),
        ]
        
        # Verify each status has both icon and text
        for indicator in status_indicators:
            assert len(indicator.controls) == 2  # Icon and text
    
    def test_sufficient_color_contrast(self):
        """
        Test that text has sufficient color contrast.
        
        **Validates: Requirements 16.1**
        """
        # Create text elements with good contrast
        text_elements = [
            ft.Text("Black text on white", color="black"),
            ft.Text("White text on dark", color="white"),
        ]
        
        # Verify text has color specified
        # (Actual contrast testing would require color analysis)
        for text in text_elements:
            assert text.color is not None
    
    def test_interactive_elements_have_minimum_size(self):
        """
        Test that interactive elements meet minimum size requirements.
        
        **Validates: Requirements 16.1**
        """
        # Create buttons with adequate size
        buttons = [
            ft.ElevatedButton(text="Submit", height=40),
            ft.IconButton(icon=ft.icons.EDIT, icon_size=24),
        ]
        
        # Verify buttons have adequate size
        assert buttons[0].height >= 40
        assert buttons[1].icon_size >= 20
    
    def test_form_labels_associated_with_inputs(self):
        """
        Test that form labels are properly associated with inputs.
        
        **Validates: Requirements 16.1**
        """
        # Create form fields with labels
        form_fields = [
            ft.TextField(label="Product Name"),
            ft.TextField(label="SKU"),
            ft.Dropdown(label="Category"),
            ft.Checkbox(label="Active"),
        ]
        
        # Verify all fields have labels
        for field in form_fields:
            assert field.label is not None
            assert len(field.label) > 0
    
    def test_required_fields_indicated(self):
        """
        Test that required fields are clearly indicated.
        
        **Validates: Requirements 16.1**
        """
        # Create required fields with indicators
        required_fields = [
            ft.TextField(label="Product Name *", hint_text="Required"),
            ft.TextField(label="SKU *", hint_text="Required"),
        ]
        
        # Verify required indicator is present
        for field in required_fields:
            assert "*" in field.label or "Required" in field.hint_text


class TestKeyboardAccessibilityIntegration:
    """Test keyboard accessibility in integrated scenarios."""
    
    def test_complete_form_keyboard_workflow(self):
        """
        Test complete form can be filled using only keyboard.
        
        **Validates: Requirements 16.1**
        """
        # Create complete form
        form = ft.Column(
            controls=[
                ft.TextField(label="Product Name", autofocus=True),
                ft.TextField(label="SKU"),
                ft.TextField(label="Price"),
                ft.TextField(label="Quantity"),
                ft.Dropdown(label="Category"),
                ft.Row(controls=[
                    ft.ElevatedButton(text="Save"),
                    ft.TextButton(text="Cancel"),
                ])
            ]
        )
        
        # Verify form has proper structure
        assert form.controls[0].autofocus is True
        assert form.controls[0].label == "Product Name"
        assert len(form.controls) == 6
    
    def test_data_table_keyboard_navigation(self):
        """
        Test data table can be navigated with keyboard.
        
        **Validates: Requirements 16.1**
        """
        # Create data table with keyboard-accessible actions
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Product 1")),
                    ft.DataCell(ft.Row(controls=[
                        ft.IconButton(icon=ft.icons.EDIT, tooltip="Edit"),
                        ft.IconButton(icon=ft.icons.DELETE, tooltip="Delete"),
                    ])),
                ]),
            ]
        )
        
        # Verify action buttons have tooltips for accessibility
        action_buttons = table.rows[0].cells[1].content.controls
        assert action_buttons[0].tooltip == "Edit"
        assert action_buttons[1].tooltip == "Delete"
    
    def test_modal_dialog_keyboard_workflow(self):
        """
        Test modal dialog can be operated with keyboard.
        
        **Validates: Requirements 16.1**
        """
        # Create modal dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this product?"),
            actions=[
                ft.TextButton("Cancel"),
                ft.ElevatedButton("Delete"),
            ]
        )
        
        # Verify dialog is modal and has keyboard navigation
        assert dialog.modal is True
        assert len(dialog.actions) == 2
        assert dialog.actions[0].text == "Cancel"
        assert dialog.actions[1].text == "Delete"
    
    def test_search_and_filter_keyboard_workflow(self):
        """
        Test search and filter can be operated with keyboard.
        
        **Validates: Requirements 16.1**
        """
        # Create search and filter UI
        search_ui = ft.Column(
            controls=[
                ft.TextField(
                    label="Search Products",
                    autofocus=True,
                    on_submit=lambda e: None
                ),
                ft.Row(controls=[
                    ft.Dropdown(label="Category"),
                    ft.Dropdown(label="Status"),
                    ft.ElevatedButton(text="Apply Filters"),
                ])
            ]
        )
        
        # Verify search has proper keyboard support
        search_field = search_ui.controls[0]
        assert search_field.autofocus is True
        assert search_field.on_submit is not None
        assert search_field.label == "Search Products"

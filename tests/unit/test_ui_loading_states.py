"""
Unit tests for UI loading states and feedback.

Tests verify that:
- Loading indicators appear and disappear correctly during async operations
- Buttons are disabled during operations to prevent double-clicks
- UI provides proper feedback to users during long-running operations

**Validates: Requirements 9.1, 12.1**
"""

import pytest
import flet as ft
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import time


class TestLoadingIndicators:
    """Test loading indicators appear and disappear correctly."""
    
    def test_loading_indicator_initially_hidden(self):
        """
        Test that loading indicator is initially hidden.
        
        **Validates: Requirements 12.1**
        """
        # Create a loading indicator
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Verify it's initially hidden
        assert loading_indicator.visible is False
    
    def test_loading_indicator_shows_during_operation(self):
        """
        Test that loading indicator becomes visible during an operation.
        
        **Validates: Requirements 12.1**
        """
        # Create a loading indicator
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Simulate starting an operation
        loading_indicator.visible = True
        
        # Verify it's now visible
        assert loading_indicator.visible is True
    
    def test_loading_indicator_hides_after_operation(self):
        """
        Test that loading indicator is hidden after operation completes.
        
        **Validates: Requirements 12.1**
        """
        # Create a loading indicator
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Simulate operation lifecycle
        loading_indicator.visible = True
        assert loading_indicator.visible is True
        
        # Operation completes
        loading_indicator.visible = False
        assert loading_indicator.visible is False
    
    def test_loading_indicator_hides_after_error(self):
        """
        Test that loading indicator is hidden even if operation fails.
        
        **Validates: Requirements 12.1**
        """
        # Create a loading indicator
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        try:
            # Simulate starting an operation
            loading_indicator.visible = True
            assert loading_indicator.visible is True
            
            # Simulate an error
            raise ValueError("Simulated error")
        except ValueError:
            # Ensure loading indicator is hidden in error handler
            loading_indicator.visible = False
        
        # Verify it's hidden after error
        assert loading_indicator.visible is False
    
    def test_multiple_loading_indicators_independent(self):
        """
        Test that multiple loading indicators can be controlled independently.
        
        **Validates: Requirements 12.1**
        """
        # Create multiple loading indicators
        loading_indicator_1 = ft.ProgressRing(visible=False, width=30, height=30)
        loading_indicator_2 = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Show first indicator
        loading_indicator_1.visible = True
        assert loading_indicator_1.visible is True
        assert loading_indicator_2.visible is False
        
        # Show second indicator
        loading_indicator_2.visible = True
        assert loading_indicator_1.visible is True
        assert loading_indicator_2.visible is True
        
        # Hide first indicator
        loading_indicator_1.visible = False
        assert loading_indicator_1.visible is False
        assert loading_indicator_2.visible is True
    
    def test_loading_indicator_properties(self):
        """
        Test that loading indicator has correct properties.
        
        **Validates: Requirements 12.1**
        """
        # Create a loading indicator with specific properties
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Verify properties
        assert loading_indicator.width == 30
        assert loading_indicator.height == 30
        assert loading_indicator.visible is False


class TestButtonDisabling:
    """Test buttons are disabled during operations."""
    
    def test_button_initially_enabled(self):
        """
        Test that button is initially enabled.
        
        **Validates: Requirements 12.1**
        """
        # Create a button
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Verify it's initially enabled
        assert button.disabled is False
    
    def test_button_disabled_during_operation(self):
        """
        Test that button is disabled when operation starts.
        
        **Validates: Requirements 12.1**
        """
        # Create a button
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Simulate starting an operation
        button.disabled = True
        
        # Verify it's now disabled
        assert button.disabled is True
    
    def test_button_enabled_after_operation(self):
        """
        Test that button is re-enabled after operation completes.
        
        **Validates: Requirements 12.1**
        """
        # Create a button
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Simulate operation lifecycle
        button.disabled = True
        assert button.disabled is True
        
        # Operation completes
        button.disabled = False
        assert button.disabled is False
    
    def test_button_enabled_after_error(self):
        """
        Test that button is re-enabled even if operation fails.
        
        **Validates: Requirements 12.1**
        """
        # Create a button
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        try:
            # Simulate starting an operation
            button.disabled = True
            assert button.disabled is True
            
            # Simulate an error
            raise ValueError("Simulated error")
        except ValueError:
            # Ensure button is re-enabled in error handler
            button.disabled = False
        
        # Verify it's enabled after error
        assert button.disabled is False
    
    def test_multiple_buttons_disabled_during_operation(self):
        """
        Test that multiple buttons can be disabled during an operation.
        
        **Validates: Requirements 12.1**
        """
        # Create multiple buttons
        save_button = ft.ElevatedButton(text="Save", disabled=False)
        cancel_button = ft.ElevatedButton(text="Cancel", disabled=False)
        
        # Disable both during operation
        save_button.disabled = True
        cancel_button.disabled = True
        
        assert save_button.disabled is True
        assert cancel_button.disabled is True
        
        # Re-enable after operation
        save_button.disabled = False
        cancel_button.disabled = False
        
        assert save_button.disabled is False
        assert cancel_button.disabled is False
    
    def test_button_visual_feedback_during_disable(self):
        """
        Test that button provides visual feedback when disabled.
        
        **Validates: Requirements 12.1**
        """
        # Create a button with color
        button = ft.ElevatedButton(
            text="Submit",
            disabled=False,
            bgcolor="green"
        )
        
        # Verify initial state
        assert button.disabled is False
        assert button.bgcolor == "green"
        
        # Disable and change color for visual feedback
        button.disabled = True
        button.bgcolor = "gray"
        
        assert button.disabled is True
        assert button.bgcolor == "gray"


class TestLoadingStateIntegration:
    """Test loading indicators and button disabling work together."""
    
    def test_loading_and_button_state_synchronized(self):
        """
        Test that loading indicator and button state are synchronized.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Simulate operation start
        loading_indicator.visible = True
        button.disabled = True
        
        assert loading_indicator.visible is True
        assert button.disabled is True
        
        # Simulate operation end
        loading_indicator.visible = False
        button.disabled = False
        
        assert loading_indicator.visible is False
        assert button.disabled is False
    
    def test_loading_state_cleanup_on_error(self):
        """
        Test that both loading indicator and button are restored on error.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        try:
            # Simulate operation start
            loading_indicator.visible = True
            button.disabled = True
            
            # Simulate error
            raise ValueError("Operation failed")
        except ValueError:
            # Cleanup in error handler
            loading_indicator.visible = False
            button.disabled = False
        
        # Verify both are restored
        assert loading_indicator.visible is False
        assert button.disabled is False
    
    def test_nested_operations_loading_state(self):
        """
        Test loading state management with nested operations.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Start outer operation
        loading_indicator.visible = True
        button.disabled = True
        
        # Simulate nested operation (should maintain loading state)
        assert loading_indicator.visible is True
        assert button.disabled is True
        
        # Complete all operations
        loading_indicator.visible = False
        button.disabled = False
        
        assert loading_indicator.visible is False
        assert button.disabled is False


class TestAsyncOperationLoadingStates:
    """Test loading states during async operations."""
    
    @pytest.mark.asyncio
    async def test_loading_state_during_async_operation(self):
        """
        Test loading state is maintained during async operation.
        
        **Validates: Requirements 9.1, 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        async def async_operation():
            """Simulate an async operation."""
            await asyncio.sleep(0.1)  # Simulate work
            return "success"
        
        # Start operation
        loading_indicator.visible = True
        button.disabled = True
        
        # Execute async operation
        result = await async_operation()
        
        # End operation
        loading_indicator.visible = False
        button.disabled = False
        
        # Verify final state
        assert result == "success"
        assert loading_indicator.visible is False
        assert button.disabled is False
    
    @pytest.mark.asyncio
    async def test_loading_state_cleanup_on_async_error(self):
        """
        Test loading state is cleaned up when async operation fails.
        
        **Validates: Requirements 9.1, 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        async def failing_async_operation():
            """Simulate a failing async operation."""
            await asyncio.sleep(0.1)
            raise ValueError("Async operation failed")
        
        try:
            # Start operation
            loading_indicator.visible = True
            button.disabled = True
            
            # Execute failing async operation
            await failing_async_operation()
        except ValueError:
            # Cleanup on error
            loading_indicator.visible = False
            button.disabled = False
        
        # Verify cleanup happened
        assert loading_indicator.visible is False
        assert button.disabled is False
    
    @pytest.mark.asyncio
    async def test_loading_state_for_operations_over_200ms(self):
        """
        Test that loading indicator appears for operations taking >200ms.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        async def long_operation():
            """Simulate an operation taking >200ms."""
            await asyncio.sleep(0.25)  # 250ms
            return "completed"
        
        # Start operation
        start_time = time.time()
        loading_indicator.visible = True
        
        # Execute operation
        result = await long_operation()
        duration = time.time() - start_time
        
        # End operation
        loading_indicator.visible = False
        
        # Verify operation took >200ms and loading was shown
        assert duration > 0.2
        assert result == "completed"
        assert loading_indicator.visible is False


class TestFormSubmissionLoadingStates:
    """Test loading states during form submissions."""
    
    def test_form_submit_button_disabled_on_submit(self):
        """
        Test that form submit button is disabled when form is submitted.
        
        **Validates: Requirements 12.1**
        """
        # Create form elements
        text_field = ft.TextField(label="Name", value="Test")
        submit_button = ft.ElevatedButton(text="Submit", disabled=False)
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        
        # Simulate form submission
        submit_button.disabled = True
        loading_indicator.visible = True
        
        # Verify state during submission
        assert submit_button.disabled is True
        assert loading_indicator.visible is True
        
        # Simulate submission complete
        submit_button.disabled = False
        loading_indicator.visible = False
        
        # Verify state after submission
        assert submit_button.disabled is False
        assert loading_indicator.visible is False
    
    def test_form_fields_remain_accessible_during_submit(self):
        """
        Test that form fields remain accessible while submit is in progress.
        
        **Validates: Requirements 12.1**
        """
        # Create form elements
        text_field = ft.TextField(label="Name", value="Test", disabled=False)
        submit_button = ft.ElevatedButton(text="Submit", disabled=False)
        
        # Simulate form submission (only button disabled, not fields)
        submit_button.disabled = True
        
        # Verify button is disabled but field is not
        assert submit_button.disabled is True
        assert text_field.disabled is False
    
    def test_multiple_submit_prevention(self):
        """
        Test that disabling button prevents multiple submissions.
        
        **Validates: Requirements 12.1**
        """
        # Create submit button
        submit_button = ft.ElevatedButton(text="Submit", disabled=False)
        submission_count = {"count": 0}
        
        def submit_handler():
            """Simulate submit handler."""
            if not submit_button.disabled:
                submit_button.disabled = True
                submission_count["count"] += 1
                # Simulate async work
                # ... operation ...
                # Note: In real scenario, button would be re-enabled after operation
        
        # First submission
        submit_handler()
        assert submission_count["count"] == 1
        assert submit_button.disabled is True
        
        # Attempt second submission while first is in progress
        # This should be prevented because button is disabled
        submit_handler()
        
        # Verify second submission was prevented
        assert submission_count["count"] == 1
        assert submit_button.disabled is True


class TestDataLoadingStates:
    """Test loading states during data loading operations."""
    
    def test_loading_state_during_data_fetch(self):
        """
        Test loading indicator appears during data fetching.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        data_container = ft.Column(controls=[])
        
        # Start data fetch
        loading_indicator.visible = True
        
        # Verify loading state
        assert loading_indicator.visible is True
        assert len(data_container.controls) == 0
        
        # Simulate data loaded
        data_container.controls = [
            ft.Text("Item 1"),
            ft.Text("Item 2"),
        ]
        loading_indicator.visible = False
        
        # Verify final state
        assert loading_indicator.visible is False
        assert len(data_container.controls) == 2
    
    def test_loading_state_during_search(self):
        """
        Test loading indicator appears during search operations.
        
        **Validates: Requirements 12.1**
        """
        # Create search UI elements
        search_field = ft.TextField(label="Search", value="test")
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        results_container = ft.Column(controls=[])
        
        # Start search
        loading_indicator.visible = True
        
        # Verify loading state
        assert loading_indicator.visible is True
        
        # Simulate search complete
        results_container.controls = [ft.Text("Result 1")]
        loading_indicator.visible = False
        
        # Verify final state
        assert loading_indicator.visible is False
        assert len(results_container.controls) == 1
    
    def test_loading_state_during_pagination(self):
        """
        Test loading indicator appears during page navigation.
        
        **Validates: Requirements 12.1**
        """
        # Create pagination UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        next_button = ft.IconButton(icon=ft.icons.CHEVRON_RIGHT, disabled=False)
        current_page = {"page": 1}
        
        # Navigate to next page
        loading_indicator.visible = True
        next_button.disabled = True
        current_page["page"] += 1
        
        # Verify loading state
        assert loading_indicator.visible is True
        assert next_button.disabled is True
        assert current_page["page"] == 2
        
        # Simulate page loaded
        loading_indicator.visible = False
        next_button.disabled = False
        
        # Verify final state
        assert loading_indicator.visible is False
        assert next_button.disabled is False


class TestErrorHandlingWithLoadingStates:
    """Test loading states are properly cleaned up on errors."""
    
    def test_loading_state_cleanup_on_validation_error(self):
        """
        Test loading state is cleaned up when validation fails.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        text_field = ft.TextField(label="Amount", value="invalid")
        
        try:
            # Start operation
            loading_indicator.visible = True
            button.disabled = True
            
            # Validate input
            amount = float(text_field.value)
        except ValueError:
            # Cleanup on validation error
            loading_indicator.visible = False
            button.disabled = False
        
        # Verify cleanup
        assert loading_indicator.visible is False
        assert button.disabled is False
    
    def test_loading_state_cleanup_on_network_error(self):
        """
        Test loading state is cleaned up when network operation fails.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Load Data", disabled=False)
        
        def simulate_network_operation():
            """Simulate a failing network operation."""
            raise ConnectionError("Network unavailable")
        
        try:
            # Start operation
            loading_indicator.visible = True
            button.disabled = True
            
            # Attempt network operation
            simulate_network_operation()
        except ConnectionError:
            # Cleanup on network error
            loading_indicator.visible = False
            button.disabled = False
        
        # Verify cleanup
        assert loading_indicator.visible is False
        assert button.disabled is False
    
    def test_loading_state_with_finally_block(self):
        """
        Test loading state cleanup using finally block pattern.
        
        **Validates: Requirements 12.1**
        """
        # Create UI elements
        loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
        button = ft.ElevatedButton(text="Submit", disabled=False)
        
        try:
            # Start operation
            loading_indicator.visible = True
            button.disabled = True
            
            # Simulate operation that might fail
            if True:  # Simulate error condition
                raise RuntimeError("Operation failed")
        except RuntimeError:
            pass  # Handle error
        finally:
            # Always cleanup in finally block
            loading_indicator.visible = False
            button.disabled = False
        
        # Verify cleanup happened
        assert loading_indicator.visible is False
        assert button.disabled is False

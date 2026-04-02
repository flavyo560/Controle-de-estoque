"""
Bug Condition Exploration Test for NavigationRail Layout Error

**Validates: Requirements 2.1, 2.2, 2.3**

This test demonstrates the NavigationRail layout bug that occurs when:
- innerContainer.expand == True
- outerContainer.expand == True (or implicit)
- outerContainer.height == None
- NavigationRail is nested in ambiguous sizing hierarchy

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

The test encodes the expected behavior - it will validate the fix when it passes after implementation.
"""

import pytest
from hypothesis import given, strategies as st, settings
import flet as ft
import re


def isBugCondition(inner_expand: bool, outer_height: bool, outer_expand: bool) -> bool:
    """
    Determines if a NavigationRail configuration triggers the bug.
    
    Args:
        inner_expand: Whether inner Container has expand=True
        outer_height: Whether outer Container has fixed height
        outer_expand: Whether outer Container has expand=True (or implicit)
    
    Returns:
        True if configuration triggers the bug
    """
    return (
        inner_expand == True
        and outer_height == False
        and outer_expand == True
    )


def test_navigation_rail_bug_condition_exists():
    """
    **Property 1: Fault Condition** - NavigationRail Renders Without Error
    
    This test verifies that the current main.py configuration triggers the bug.
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (proving bug exists)
    
    The test checks the actual code structure in main.py to confirm:
    1. Inner Container (wrapping nav_rail) has expand=True
    2. Outer Container (nav_rail_with_logout) has no fixed height
    3. This creates ambiguous sizing that triggers Flet error
    """
    # Read main.py to analyze the NavigationRail structure
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the nav_rail_with_logout section (around line 1874)
    # Look for the pattern: ft.Container(content=nav_rail, expand=True)
    inner_container_pattern = r'ft\.Container\s*\(\s*content\s*=\s*nav_rail\s*,\s*expand\s*=\s*True\s*\)'
    inner_has_expand = bool(re.search(inner_container_pattern, content))
    
    # Look for nav_rail_with_logout definition
    # Check if it has a fixed height parameter
    nav_rail_with_logout_section = re.search(
        r'nav_rail_with_logout\s*=\s*ft\.Container\s*\([^)]+\)',
        content,
        re.DOTALL
    )
    
    outer_has_fixed_height = False
    if nav_rail_with_logout_section:
        section_text = nav_rail_with_logout_section.group(0)
        # Check if height parameter is present
        outer_has_fixed_height = bool(re.search(r'height\s*=\s*\d+', section_text))
    
    # The bug condition exists if:
    # - Inner container has expand=True
    # - Outer container has no fixed height
    bug_condition_present = inner_has_expand and not outer_has_fixed_height
    
    # ASSERTION: The bug condition should NOT be present (expected behavior)
    # This assertion will FAIL on unfixed code, proving the bug exists
    assert not bug_condition_present, (
        f"NavigationRail bug condition detected!\n"
        f"Inner Container expand=True: {inner_has_expand}\n"
        f"Outer Container has fixed height: {outer_has_fixed_height}\n"
        f"This configuration causes Flet error: 'Control should be unambiguous. "
        f"Either set 'expand', 'property', set a 'fixed' 'height' on root NavigationRail "
        f"inside another control with a fixed height.'\n"
        f"Expected: Inner Container should NOT have expand=True OR Outer Container should have fixed height"
    )


@settings(max_examples=50)
@given(
    inner_expand=st.booleans(),
    outer_height=st.booleans(),
    outer_expand=st.booleans()
)
def test_navigation_rail_configuration_property(inner_expand: bool, outer_height: bool, outer_expand: bool):
    """
    **Property 1: Fault Condition** - NavigationRail Renders Without Error
    
    Property-based test that verifies NavigationRail configurations.
    
    For any configuration where isBugCondition is False (non-buggy configurations),
    the NavigationRail should render without errors.
    
    For configurations where isBugCondition is True (buggy configurations),
    the NavigationRail should either:
    - Be fixed (inner_expand removed or outer_height added)
    - Or produce an error (on unfixed code)
    
    EXPECTED OUTCOME on UNFIXED code:
    - Non-buggy configurations: PASS
    - Buggy configurations: FAIL (proving bug exists)
    
    EXPECTED OUTCOME on FIXED code:
    - All configurations: PASS (bug is fixed)
    """
    is_bug_config = isBugCondition(inner_expand, outer_height, outer_expand)
    
    # Read current main.py configuration
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check actual configuration in main.py
    inner_container_pattern = r'ft\.Container\s*\(\s*content\s*=\s*nav_rail\s*,\s*expand\s*=\s*True\s*\)'
    actual_inner_has_expand = bool(re.search(inner_container_pattern, content))
    
    nav_rail_with_logout_section = re.search(
        r'nav_rail_with_logout\s*=\s*ft\.Container\s*\([^)]+\)',
        content,
        re.DOTALL
    )
    
    actual_outer_has_fixed_height = False
    if nav_rail_with_logout_section:
        section_text = nav_rail_with_logout_section.group(0)
        actual_outer_has_fixed_height = bool(re.search(r'height\s*=\s*\d+', section_text))
    
    actual_bug_condition = actual_inner_has_expand and not actual_outer_has_fixed_height
    
    # If the current code has the bug condition, this test should fail
    # (on unfixed code, this proves the bug exists)
    if is_bug_config:
        # For buggy configurations, assert that the code is fixed
        # This will FAIL on unfixed code
        assert not actual_bug_condition, (
            f"Bug configuration detected in main.py!\n"
            f"Test configuration: inner_expand={inner_expand}, outer_height={outer_height}, outer_expand={outer_expand}\n"
            f"Actual code: inner_expand={actual_inner_has_expand}, outer_fixed_height={actual_outer_has_fixed_height}\n"
            f"The code has the bug condition that causes Flet error.\n"
            f"Expected: Code should be fixed (remove inner expand or add outer height)"
        )


def test_navigation_rail_error_message_detection():
    """
    **Property 1: Fault Condition** - NavigationRail Renders Without Error
    
    This test attempts to detect the actual Flet error message that appears
    when the NavigationRail bug is triggered.
    
    EXPECTED OUTCOME: This test documents the error (may not fail directly,
    but provides evidence of the bug through error message detection)
    
    Note: This test checks for the error pattern in the code structure.
    The actual runtime error would appear when running the application.
    """
    # Read main.py
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for the problematic pattern
    inner_container_pattern = r'ft\.Container\s*\(\s*content\s*=\s*nav_rail\s*,\s*expand\s*=\s*True\s*\)'
    has_problematic_pattern = bool(re.search(inner_container_pattern, content))
    
    if has_problematic_pattern:
        # Document the bug condition
        error_message = (
            "COUNTEREXAMPLE FOUND:\n"
            "===================\n"
            "The code contains the pattern: ft.Container(content=nav_rail, expand=True)\n"
            "This pattern, when nested inside nav_rail_with_logout without fixed height,\n"
            "causes Flet 0.25.0 to display the error:\n"
            "'Error displaying NavigationRail - Control should be unambiguous. "
            "Either set 'expand', 'property', set a 'fixed' 'height' on root NavigationRail "
            "inside another control with a fixed height.'\n\n"
            "Visual symptoms:\n"
            "- Error message displayed in the UI\n"
            "- NavigationRail and main content may overlap\n"
            "- Layout appears disorganized\n\n"
            "Location: main.py, approximately line 1876\n"
            "Pattern: Container(expand=True) → Column → Container(expand=True) with nav_rail\n"
        )
        
        # This assertion will FAIL on unfixed code, documenting the counterexample
        assert not has_problematic_pattern, error_message


if __name__ == "__main__":
    # Run the tests to demonstrate the bug
    print("Running Bug Condition Exploration Tests...")
    print("=" * 60)
    print("EXPECTED: These tests FAIL on unfixed code (proving bug exists)")
    print("=" * 60)
    
    try:
        test_navigation_rail_bug_condition_exists()
        print("✓ test_navigation_rail_bug_condition_exists PASSED")
    except AssertionError as e:
        print("✗ test_navigation_rail_bug_condition_exists FAILED (expected)")
        print(f"  Error: {e}")
    
    print()
    
    try:
        test_navigation_rail_error_message_detection()
        print("✓ test_navigation_rail_error_message_detection PASSED")
    except AssertionError as e:
        print("✗ test_navigation_rail_error_message_detection FAILED (expected)")
        print(f"  Error: {e}")

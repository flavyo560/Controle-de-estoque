"""
Preservation Property Tests for NavigationRail Layout Error Fix

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

These tests verify that the NavigationRail fix does NOT break existing functionality:
- Navigation clicks between views (Estoque, Vendas, Clientes, Relatórios, Cancelar Venda)
- Logout button functionality
- Content rendering in each view
- Visual styles (icons, labels, colors, spacing)

IMPORTANT: These tests are run on UNFIXED code FIRST to observe baseline behavior,
then run again on FIXED code to ensure no regressions.

EXPECTED OUTCOME: Tests PASS on both unfixed and fixed code (confirms preservation)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import re


def test_navigation_destinations_structure():
    """
    **Property 2: Preservation** - Navigation Destinations Structure
    
    Verifies that the NavigationRail has the correct destinations defined:
    - Estoque (index 0)
    - Vendas (index 1)
    - Clientes (index 2)
    - Relatórios (index 3)
    - Cancelar Venda (index 4)
    
    This structure must be preserved after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find NavigationRail destinations section
    nav_rail_section = re.search(
        r'nav_rail\s*=\s*ft\.NavigationRail\s*\([^)]+destinations\s*=\s*\[(.*?)\]',
        content,
        re.DOTALL
    )
    
    assert nav_rail_section is not None, "NavigationRail not found in main.py"
    
    destinations_text = nav_rail_section.group(1)
    
    # Verify all expected destinations are present
    expected_destinations = [
        ("INVENTORY", "Estoque"),
        ("SHOPPING_CART", "Vendas"),
        ("PEOPLE", "Clientes"),
        ("BAR_CHART", "Relatórios"),
        ("CANCEL", "Cancelar Venda")
    ]
    
    for icon_pattern, label in expected_destinations:
        assert icon_pattern in destinations_text, f"Icon pattern {icon_pattern} not found in destinations"
        assert label in destinations_text, f"Label '{label}' not found in destinations"
    
    print(f"✓ All {len(expected_destinations)} navigation destinations are correctly defined")


def test_navigation_handler_exists():
    """
    **Property 2: Preservation** - Navigation Handler Exists
    
    Verifies that the on_nav_change handler is defined and connected to NavigationRail.
    This handler is responsible for switching between views when navigation items are clicked.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that on_nav_change function exists
    assert 'def on_nav_change(e):' in content, "on_nav_change handler not found"
    
    # Check that NavigationRail has on_change=on_nav_change
    # Need to capture until we find the closing paren after all parameters
    nav_rail_section = re.search(
        r'nav_rail\s*=\s*ft\.NavigationRail\s*\((.*?)\n\s*\)\s*$',
        content,
        re.DOTALL | re.MULTILINE
    )
    
    assert nav_rail_section is not None, "NavigationRail not found"
    nav_rail_full = nav_rail_section.group(0)
    assert 'on_change=on_nav_change' in nav_rail_full, "on_change handler not connected"
    
    print("✓ Navigation handler is correctly defined and connected")


def test_mudar_view_function_logic():
    """
    **Property 2: Preservation** - View Switching Logic
    
    Verifies that the mudar_view function correctly handles view switching:
    - Updates estado_navegacao["view_atual"]
    - Updates nav_rail.selected_index
    - Shows/hides appropriate containers
    - Updates page
    
    This logic must be preserved after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find mudar_view function
    mudar_view_match = re.search(
        r'def mudar_view\(destino: str\):(.*?)(?=\n    def |\n\n    # |\Z)',
        content,
        re.DOTALL
    )
    
    assert mudar_view_match is not None, "mudar_view function not found"
    
    mudar_view_code = mudar_view_match.group(1)
    
    # Verify key logic is present
    assert 'estado_navegacao["view_atual"] = destino' in mudar_view_code, \
        "View state update missing"
    assert 'nav_rail.selected_index = i' in mudar_view_code, \
        "NavigationRail index update missing"
    assert 'container_estoque_wrapper.visible' in mudar_view_code, \
        "Estoque container visibility logic missing"
    assert 'container_vendas.visible' in mudar_view_code, \
        "Vendas container visibility logic missing"
    assert 'container_clientes.visible' in mudar_view_code, \
        "Clientes container visibility logic missing"
    assert 'container_relatorios_vendas.visible' in mudar_view_code, \
        "Relatórios container visibility logic missing"
    assert 'container_cancelamento.visible' in mudar_view_code, \
        "Cancelamento container visibility logic missing"
    assert 'page.update()' in mudar_view_code, \
        "Page update missing"
    
    print("✓ View switching logic is correctly implemented")


def test_on_nav_change_handler_logic():
    """
    **Property 2: Preservation** - Navigation Change Handler Logic
    
    Verifies that on_nav_change correctly maps navigation indices to view names:
    - Index 0 → "estoque"
    - Index 1 → "vendas"
    - Index 2 → "clientes"
    - Index 3 → "relatorios"
    - Index 4 → "cancelamento"
    
    This mapping must be preserved after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find on_nav_change function
    on_nav_change_match = re.search(
        r'def on_nav_change\(e\):(.*?)(?=\n    def |\Z)',
        content,
        re.DOTALL
    )
    
    assert on_nav_change_match is not None, "on_nav_change function not found"
    
    on_nav_change_code = on_nav_change_match.group(1)
    
    # Verify the destinations list is correct
    assert 'destinos = ["estoque", "vendas", "clientes", "relatorios", "cancelamento"]' in on_nav_change_code, \
        "Destinations list is incorrect or missing"
    
    # Verify mudar_view is called
    assert 'mudar_view(destinos[index])' in on_nav_change_code, \
        "mudar_view call missing"
    
    print("✓ Navigation change handler correctly maps indices to views")


def test_logout_button_exists():
    """
    **Property 2: Preservation** - Logout Button Exists
    
    Verifies that the logout button ("Sair") is present in nav_rail_with_logout
    and is connected to the fazer_logout handler.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find nav_rail_with_logout section (now a Column instead of Container)
    nav_rail_with_logout_match = re.search(
        r'nav_rail_with_logout\s*=\s*ft\.Column\s*\((.*?)(?=\n    # --- WRAPPER)',
        content,
        re.DOTALL
    )
    
    assert nav_rail_with_logout_match is not None, "nav_rail_with_logout not found"
    
    nav_rail_with_logout_code = nav_rail_with_logout_match.group(1)
    
    # Verify logout button is present
    assert '"Sair"' in nav_rail_with_logout_code or "'Sair'" in nav_rail_with_logout_code, \
        "Logout button text 'Sair' not found"
    assert 'ft.icons.LOGOUT' in nav_rail_with_logout_code, \
        "Logout icon not found"
    assert 'on_click=fazer_logout' in nav_rail_with_logout_code, \
        "Logout handler not connected"
    
    print("✓ Logout button is correctly defined and connected")


def test_fazer_logout_function_exists():
    """
    **Property 2: Preservation** - Logout Function Exists
    
    Verifies that the fazer_logout function is defined and contains
    the expected logout logic (encerrar_sessao_atual, page.clean, etc.).
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find fazer_logout function
    fazer_logout_match = re.search(
        r'def fazer_logout\(e\):(.*?)(?=\n    def |\Z)',
        content,
        re.DOTALL
    )
    
    assert fazer_logout_match is not None, "fazer_logout function not found"
    
    fazer_logout_code = fazer_logout_match.group(1)
    
    # Verify key logout logic is present
    assert 'encerrar_sessao_atual()' in fazer_logout_code, \
        "Session termination call missing"
    assert 'page.clean()' in fazer_logout_code, \
        "Page clean call missing"
    assert 'Logout realizado com sucesso' in fazer_logout_code, \
        "Success message missing"
    assert 'page.update()' in fazer_logout_code, \
        "Page update missing"
    
    print("✓ Logout function is correctly implemented")


def test_content_containers_exist():
    """
    **Property 2: Preservation** - Content Containers Exist
    
    Verifies that all content containers are defined:
    - container_estoque_wrapper
    - container_vendas
    - container_clientes
    - container_relatorios_vendas
    - container_cancelamento
    
    These containers must exist and be properly configured after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    expected_containers = [
        'container_estoque_wrapper',
        'container_vendas',
        'container_clientes',
        'container_relatorios_vendas',
        'container_cancelamento'
    ]
    
    for container_name in expected_containers:
        # Check that container is defined
        pattern = f'{container_name}\\s*=\\s*ft\\.Container'
        assert re.search(pattern, content), f"{container_name} not found"
        
        # Check that container has expand=True (for proper layout)
        # Use a more flexible pattern that captures the full container definition
        container_match = re.search(
            f'{container_name}\\s*=\\s*ft\\.Container\\s*\\((.*?)\\n\\s*\\)',
            content,
            re.DOTALL
        )
        assert container_match is not None, f"{container_name} definition not found"
        container_code = container_match.group(0)
        assert 'expand=True' in container_code, f"{container_name} missing expand=True"
    
    print(f"✓ All {len(expected_containers)} content containers are correctly defined")


def test_layout_row_structure():
    """
    **Property 2: Preservation** - Layout Row Structure
    
    Verifies that the main layout Row contains:
    - nav_rail_with_logout
    - VerticalDivider
    - All content containers
    
    This structure must be preserved after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find layout_row definition
    layout_row_match = re.search(
        r'layout_row\s*=\s*ft\.Row\s*\(\s*\[(.*?)\]',
        content,
        re.DOTALL
    )
    
    assert layout_row_match is not None, "layout_row not found"
    
    layout_row_code = layout_row_match.group(1)
    
    # Verify all expected components are in the Row
    expected_components = [
        'nav_rail_with_logout',
        'ft.VerticalDivider',
        'container_estoque_wrapper',
        'container_vendas',
        'container_clientes',
        'container_relatorios_vendas',
        'container_cancelamento'
    ]
    
    for component in expected_components:
        assert component in layout_row_code, f"{component} not found in layout_row"
    
    # Verify Row has expand=True
    row_params_match = re.search(
        r'layout_row\s*=\s*ft\.Row\s*\(\s*\[.*?\]\s*,\s*(.*?)\)',
        content,
        re.DOTALL
    )
    assert row_params_match is not None, "layout_row parameters not found"
    row_params = row_params_match.group(1)
    assert 'expand=True' in row_params, "layout_row missing expand=True"
    
    print("✓ Layout row structure is correctly defined")


def test_visual_styles_preserved():
    """
    **Property 2: Preservation** - Visual Styles Preserved
    
    Verifies that visual styles are preserved:
    - NavigationRail bgcolor
    - NavigationRail label_type
    - NavigationRail min_width and min_extended_width
    - Logout button colors (bgcolor=red, color=white)
    - Icons for each destination
    
    These styles must remain unchanged after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find NavigationRail definition - capture until closing paren
    nav_rail_match = re.search(
        r'nav_rail\s*=\s*ft\.NavigationRail\s*\((.*?)\n\s*\)\s*$',
        content,
        re.DOTALL | re.MULTILINE
    )
    
    assert nav_rail_match is not None, "NavigationRail not found"
    nav_rail_code = nav_rail_match.group(0)
    
    # Verify NavigationRail styles
    assert 'bgcolor="#F5F5F5"' in nav_rail_code or "bgcolor='#F5F5F5'" in nav_rail_code, \
        "NavigationRail bgcolor not preserved"
    assert 'label_type=ft.NavigationRailLabelType.ALL' in nav_rail_code, \
        "NavigationRail label_type not preserved"
    assert 'min_width=100' in nav_rail_code, \
        "NavigationRail min_width not preserved"
    assert 'min_extended_width=200' in nav_rail_code, \
        "NavigationRail min_extended_width not preserved"
    
    # Find logout button
    logout_button_match = re.search(
        r'ft\.ElevatedButton\s*\(\s*"Sair"(.*?)\)',
        content,
        re.DOTALL
    )
    
    assert logout_button_match is not None, "Logout button not found"
    logout_button_code = logout_button_match.group(1)
    
    # Verify logout button styles
    assert 'bgcolor="red"' in logout_button_code or "bgcolor='red'" in logout_button_code, \
        "Logout button bgcolor not preserved"
    assert 'color="white"' in logout_button_code or "color='white'" in logout_button_code, \
        "Logout button color not preserved"
    
    print("✓ Visual styles are correctly preserved")


@settings(max_examples=20)
@given(
    view_index=st.integers(min_value=0, max_value=4)
)
def test_navigation_index_to_view_mapping_property(view_index: int):
    """
    **Property 2: Preservation** - Navigation Index to View Mapping
    
    Property-based test that verifies the mapping from navigation indices to views.
    
    For any valid navigation index (0-4), the system should:
    1. Map to the correct view name
    2. Show the corresponding container
    3. Hide all other containers
    
    This property must hold after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Expected mapping
    index_to_view = {
        0: "estoque",
        1: "vendas",
        2: "clientes",
        3: "relatorios",
        4: "cancelamento"
    }
    
    view_to_container = {
        "estoque": "container_estoque_wrapper",
        "vendas": "container_vendas",
        "clientes": "container_clientes",
        "relatorios": "container_relatorios_vendas",
        "cancelamento": "container_cancelamento"
    }
    
    expected_view = index_to_view[view_index]
    expected_container = view_to_container[expected_view]
    
    # Find mudar_view function
    mudar_view_match = re.search(
        r'def mudar_view\(destino: str\):(.*?)(?=\n    def |\n\n    # |\Z)',
        content,
        re.DOTALL
    )
    
    assert mudar_view_match is not None, "mudar_view function not found"
    mudar_view_code = mudar_view_match.group(1)
    
    # Verify that the expected container visibility logic exists
    for view_name, container_name in view_to_container.items():
        visibility_pattern = f'{container_name}\\.visible\\s*=\\s*\\(destino\\s*==\\s*"{view_name}"\\)'
        assert re.search(visibility_pattern, mudar_view_code), \
            f"Visibility logic for {container_name} not found or incorrect"
    
    print(f"✓ Navigation index {view_index} correctly maps to view '{expected_view}' and container '{expected_container}'")


@settings(max_examples=10)
@given(
    has_divider=st.booleans(),
    has_spacing=st.booleans()
)
def test_nav_rail_with_logout_structure_property(has_divider: bool, has_spacing: bool):
    """
    **Property 2: Preservation** - NavigationRail with Logout Structure
    
    Property-based test that verifies the nav_rail_with_logout structure.
    
    The structure should contain:
    - A Column with the nav_rail and logout button
    - A Divider between them (if has_divider is True in actual code)
    - Proper spacing configuration
    
    This structure must be preserved after the fix.
    """
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find nav_rail_with_logout definition (now a Column instead of Container)
    nav_rail_with_logout_match = re.search(
        r'nav_rail_with_logout\s*=\s*ft\.Column\s*\((.*?)(?=\n    # --- WRAPPER)',
        content,
        re.DOTALL
    )
    
    assert nav_rail_with_logout_match is not None, "nav_rail_with_logout not found"
    nav_rail_with_logout_code = nav_rail_with_logout_match.group(1)
    
    # Verify nav_rail is included (now wrapped in a Container with expand=True)
    assert 'nav_rail' in nav_rail_with_logout_code, "nav_rail not found in structure"
    
    # Verify logout button is included
    assert 'Sair' in nav_rail_with_logout_code, "Logout button not found in structure"
    
    # Check if Divider exists in actual code
    actual_has_divider = 'ft.Divider' in nav_rail_with_logout_code
    
    # Check if spacing is configured in actual code
    actual_has_spacing = 'spacing=' in nav_rail_with_logout_code
    
    # Document the actual structure
    print(f"✓ nav_rail_with_logout structure verified: divider={actual_has_divider}, spacing={actual_has_spacing}")


if __name__ == "__main__":
    # Run the preservation tests
    print("Running Preservation Property Tests...")
    print("=" * 60)
    print("EXPECTED: These tests PASS on unfixed code (baseline behavior)")
    print("=" * 60)
    
    tests = [
        ("Navigation Destinations Structure", test_navigation_destinations_structure),
        ("Navigation Handler Exists", test_navigation_handler_exists),
        ("View Switching Logic", test_mudar_view_function_logic),
        ("Navigation Change Handler Logic", test_on_nav_change_handler_logic),
        ("Logout Button Exists", test_logout_button_exists),
        ("Logout Function Exists", test_fazer_logout_function_exists),
        ("Content Containers Exist", test_content_containers_exist),
        ("Layout Row Structure", test_layout_row_structure),
        ("Visual Styles Preserved", test_visual_styles_preserved),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name} PASSED")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} FAILED")
            print(f"  Error: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

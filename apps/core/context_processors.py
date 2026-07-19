"""Context processor to inject menu into all templates."""
from apps.core.menu import get_menu_for_user, is_item_active, is_any_child_active


def menu_context(request):
    if not request.user.is_authenticated:
        return {}
    
    menu = get_menu_for_user(request.user)
    
    def enrich(item):
        item.active = is_item_active(item, request)
        if item.children:
            for child in item.children:
                enrich(child)
            item.expanded = is_any_child_active(item.children, request)
        return item
    
    enriched_menu = [enrich(item) for item in menu]
    
    return {
        'main_menu': enriched_menu,
    }

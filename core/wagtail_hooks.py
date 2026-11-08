from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import QuoteRequest


class QuoteRequestViewSet(SnippetViewSet):
    model = QuoteRequest
    icon = "mail"
    menu_label = "Quote requests"
    menu_order = 150
    add_to_admin_menu = True
    list_display = ["created", "name", "phone", "product", "brand", "quantity", "emirate", "forwarded"]
    list_filter = ["product", "emirate", "installation", "forwarded"]
    search_fields = ["name", "phone", "notes"]


register_snippet(QuoteRequestViewSet)

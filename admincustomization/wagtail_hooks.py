# wagtail_hooks.py
from django.utils.html import format_html
from django.templatetags.static import static
from django.template.loader import render_to_string

from wagtail import hooks

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/wagtail-admin.css'))

@hooks.register('insert_global_admin_js')
def global_admin_js():
    return format_html('<script src="{}"></script>', static('js/homepage_minimap.js'))

# dashboard_panels.py or similar

from wagtail import hooks
from wagtail.admin.widgets import Button
from wagtail.admin.ui.components import Component
from django.utils.html import format_html
from bakerydemo.base.models import HomePage


class HomeChildrenPanel(Component):
    order = 50

    def render_html(self, parent_context):
        try:
            homepage = HomePage.objects.live().public().first()
            children = homepage.get_children().live().public()
        except Exception:
            return "<p>Error loading homepage children.</p>"

        return render_to_string("admin/home_children_panel.html", {
            "children": children,
            "homepage": homepage,
        })





# break




# wagtail_hooks.py

from django.urls import re_path, reverse
from django.http import JsonResponse, Http404
from wagtail import hooks
from wagtail.models import Page

# adjust this import to wherever your HomeChildrenPanel lives


@hooks.register("construct_homepage_panels")
def add_homepage_children_panel(request, panels):
    panels.append(HomeChildrenPanel())


# @hooks.register('register_admin_urls')
# def register_panel_api():
#     return [
#         re_path(
#             r'^pages/(?P<page_id>\d+)/panel-data/$',
#             panel_data_view,
#             name='panel_data'
#         ),
#     ]


# def panel_data_view(request, page_id):
#     # 1. Fetch the page (or 404)
#     try:
#         page = Page.objects.get(pk=page_id)
#     except Page.DoesNotExist:
#         raise Http404

#     # 2. Get the edit‑handler and build a form
#     handler = page.get_edit_handler()
#     FormClass = handler.get_form_class()
#     form = FormClass(instance=page)

#     # 3. Bind it
#     bound = handler.get_bound_panel(
#         instance=page,
#         form=form,
#         request=request,
#         prefix='panel'
#     )

#     # 4. Collect panels
#     edit_url_base = reverse("wagtailadmin_pages:edit", args=[page_id])
#     panels_out = []

#     for tab in bound.children:           # e.g. Content / Promote / Settings
#         for pnl in tab.children:         # each actual panel
#             raw = pnl.id_for_label
#             anchor = raw() if callable(raw) else raw

#             panels_out.append({
#                 "title": pnl.heading,
#                 "anchor": anchor,
#                 "url": f"{edit_url_base}#{anchor}",
#                 "icon": pnl.icon or "",
#             })

#     return JsonResponse({"panels": panels_out})
import json
from django.http import JsonResponse, Http404
from django.urls import re_path
from django.utils.html import strip_tags
from wagtail import hooks
from wagtail.models import Page
from wagtail.blocks import StreamValue
from wagtail.rich_text import RichText
from django.db.models import Field

# Optional: override default labels
FIELD_LABELS = {
    "title": "Title",
    "subtitle": "Subtitle",
    "preface": "Preface",
    "date_published": "Date article published...",
    "body": "Body",
}

def safe_serialize(value):
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if hasattr(value, "title"):
        return str(value.title)
    if hasattr(value, "name"):
        return str(value.name)
    if hasattr(value, "__str__"):
        return str(value)
    return repr(value)

def serialize_streamfield(stream_data):
    result = []

    for block in stream_data:
        value = block.value
        preview = None

        if isinstance(value, dict) or hasattr(value, "__getitem__"):
            for key in ["heading", "title", "label", "text", "heading_text", "caption"]:
                try:
                    candidate = value[key]
                    if isinstance(candidate, str) and candidate.strip():
                        preview = candidate.strip()
                        break
                except (KeyError, TypeError, AttributeError):
                    continue

        if not preview and isinstance(value, RichText):
            preview = strip_tags(value.source)

        if not preview and isinstance(value, (str, int, float)):
            preview = str(value)

        if not preview:
            preview = block.block_type

        if len(preview) > 100:
            preview = preview[:97] + "..."

        icon = getattr(block.block.meta, "icon", "placeholder")
        block_id = getattr(block, "id", None)

        result.append({
            "type": block.block_type,
            "preview": preview.strip(),
            "icon": icon,
            "href": f"#block-{block_id}-section" if block_id else None
        })

    return result

def panel_data_view(request, page_id):
    try:
        page = Page.objects.get(id=page_id).specific
    except Page.DoesNotExist:
        raise Http404("Page not found")

    data = []
    fieldset = page._meta.get_fields()

    for field in fieldset:
        if field.auto_created or not isinstance(field, Field):
            continue

        field_name = field.name
        try:
            value = getattr(page, field_name, None)
        except Exception:
            continue

        if isinstance(value, StreamValue):
            block_data = serialize_streamfield(value)
            data.append({
                "field": field_name,
                "label": FIELD_LABELS.get(field_name, field.verbose_name.title()),
                "value": block_data,
                "is_streamfield": True,
                "href": f"#panel-{field_name}-section"
            })
        else:
            data.append({
                "field": field_name,
                "label": FIELD_LABELS.get(field_name, field.verbose_name.title()),
                "value": safe_serialize(value),
                "href": f"#panel-{field_name}-section"
            })

    return JsonResponse(data, safe=False)

@hooks.register('register_admin_urls')
def register_panel_api():
    return [
        re_path(
            r'^pages/(?P<page_id>\d+)/panel-data/$',
            panel_data_view,
            name='panel_data'
        ),
    ]
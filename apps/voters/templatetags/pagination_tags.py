from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Returns the URL-encoded query string with specified parameters added/updated.
    Preserves existing query parameters except those being updated.
    
    Usage: {% query_transform page=3 %}
    """
    request = context.get('request')
    if not request:
        return ''
    
    # Copy current query params
    query = request.GET.copy()
    
    # Update with new values
    for key, value in kwargs.items():
        if value is not None and value != '':
            query[key] = value
        elif key in query:
            del query[key]
    
    return query.urlencode()


@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """
    Returns the URL for a specific page, preserving all other query parameters.
    
    Usage: {% page_url 5 %}
    """
    request = context.get('request')
    if not request:
        return f'?page={page_number}'
    
    # Copy current query params
    query = request.GET.copy()
    query['page'] = page_number
    
    return f'?{query.urlencode()}'


@register.inclusion_tag('partials/pagination.html', takes_context=True)
def render_pagination(context, page_obj, show_info=True, adjacent_pages=2):
    """
    Renders a modern pagination component.
    
    Parameters:
    - page_obj: Django Paginator page object
    - show_info: Whether to show "Showing X-Y of Z" info
    - adjacent_pages: Number of pages to show on each side of current page
    
    Usage: {% render_pagination page_obj %}
    """
    request = context.get('request')
    
    # Calculate page range to display
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages
    
    # Determine which page numbers to show
    page_numbers = []
    
    if total_pages <= 7:
        # Show all pages if 7 or fewer
        page_numbers = list(range(1, total_pages + 1))
    else:
        # Always include first page
        page_numbers.append(1)
        
        # Calculate start and end of adjacent pages
        start_page = max(2, current_page - adjacent_pages)
        end_page = min(total_pages - 1, current_page + adjacent_pages)
        
        # Add ellipsis after first page if needed
        if start_page > 2:
            page_numbers.append('...')
        
        # Add pages around current page
        for page in range(start_page, end_page + 1):
            page_numbers.append(page)
        
        # Add ellipsis before last page if needed
        if end_page < total_pages - 1:
            page_numbers.append('...')
        
        # Always include last page
        if total_pages > 1:
            page_numbers.append(total_pages)
    
    # Calculate showing range
    start_index = page_obj.start_index()
    end_index = page_obj.end_index()
    total_count = page_obj.paginator.count
    
    return {
        'page_obj': page_obj,
        'page_numbers': page_numbers,
        'show_info': show_info,
        'start_index': start_index,
        'end_index': end_index,
        'total_count': total_count,
        'request': request,
    }

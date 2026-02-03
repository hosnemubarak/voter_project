"""
Public views for Voter Slip Download (ভোটার স্লিপ ডাউনলোড).
These views are accessible without authentication.
"""
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.html import escape
from functools import wraps
import re
import json

from .models import Category, Voter


def public_rate_limit(requests_per_minute=30):
    """Rate limiting decorator for public endpoints - more restrictive than authenticated"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            
            cache_key = f'public_rate_limit:{view_func.__name__}:{ip}'
            request_count = cache.get(cache_key, 0)
            
            if request_count >= requests_per_minute:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please wait before making more requests.',
                    'retry_after': 60
                }, status=429)
            
            cache.set(cache_key, request_count + 1, 60)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def advanced_voter_search(request):
    """
    Public Voter Slip Download page (ভোটার স্লিপ ডাউনলোড).
    No authentication required. Displays filters and results for downloading voter slips.
    """
    voters = Voter.objects.select_related('category').order_by('-created_at')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    name_query = request.GET.get('name', '').strip()
    father_query = request.GET.get('father', '').strip()
    mother_query = request.GET.get('mother', '').strip()
    voter_no_query = request.GET.get('voter_no', '').strip()
    serial_query = request.GET.get('serial', '').strip()
    gender = request.GET.get('gender', '')
    
    # Hierarchical category filters
    upazila_id = request.GET.get('upazila', '')
    union_id = request.GET.get('union', '')
    voter_area_id = request.GET.get('voter_area', '')
    
    # Address filter
    address_query = request.GET.get('address', '').strip()

    # Apply search filters
    if search_query:
        voters = voters.filter(
            Q(serial__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(voter_no__icontains=search_query) |
            Q(father__icontains=search_query) |
            Q(mother__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    if name_query:
        voters = voters.filter(name__icontains=name_query)
    
    if father_query:
        voters = voters.filter(father__icontains=father_query)
    
    if mother_query:
        voters = voters.filter(mother__icontains=mother_query)
    
    if voter_no_query:
        voters = voters.filter(voter_no__icontains=voter_no_query)
    
    if serial_query:
        voters = voters.filter(serial__icontains=serial_query)
    
    if address_query:
        voters = voters.filter(address__icontains=address_query)

    # Apply hierarchical category filter
    selected_category_id = voter_area_id or union_id or upazila_id
    
    if selected_category_id:
        try:
            category = Category.objects.get(id=selected_category_id)
            descendant_ids = get_category_descendants(category)
            descendant_ids.append(category.id)
            voters = voters.filter(category_id__in=descendant_ids)
        except Category.DoesNotExist:
            pass

    if gender and gender != 'all':
        voters = voters.filter(gender=gender)

    # Check if any filter is applied
    has_filters = any([
        search_query, name_query, father_query, mother_query,
        voter_no_query, serial_query, address_query,
        upazila_id, union_id, voter_area_id, gender and gender != 'all'
    ])

    # Only show results if filters are applied (for performance and privacy)
    if has_filters:
        paginator = Paginator(voters, 50)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None

    # Get root level categories (Upazilas - Level 0)
    upazilas = Category.objects.filter(level=0).order_by('name')

    # Get selected categories for pre-populating dropdowns
    unions = []
    voter_areas = []
    
    if upazila_id:
        unions = Category.objects.filter(parent_id=upazila_id).order_by('name')
    
    if union_id:
        voter_areas = Category.objects.filter(parent_id=union_id).order_by('name')

    context = {
        'page_obj': page_obj,
        'voters': page_obj,
        'upazilas': upazilas,
        'unions': unions,
        'voter_areas': voter_areas,
        'search_query': search_query,
        'name_query': name_query,
        'father_query': father_query,
        'mother_query': mother_query,
        'voter_no_query': voter_no_query,
        'serial_query': serial_query,
        'address_query': address_query,
        'selected_upazila': upazila_id,
        'selected_union': union_id,
        'selected_voter_area': voter_area_id,
        'selected_gender': gender,
        'has_filters': has_filters,
    }
    return render(request, 'public/advanced_search.html', context)


def get_category_descendants(category):
    """Get all descendant category IDs recursively"""
    descendants = []
    children = Category.objects.filter(parent=category)
    for child in children:
        descendants.append(child.id)
        descendants.extend(get_category_descendants(child))
    return descendants


@require_GET
@public_rate_limit(requests_per_minute=60)
def public_api_categories(request):
    """Public API endpoint for category dropdown (AJAX)"""
    parent_id = request.GET.get('parent_id')
    level = request.GET.get('level')
    
    if parent_id:
        categories = Category.objects.filter(parent_id=parent_id).order_by('name')
    elif level is not None:
        categories = Category.objects.filter(level=int(level)).order_by('name')
    else:
        categories = Category.objects.filter(parent=None).order_by('name')
    
    data = [{
        'id': c.id, 
        'name': c.name, 
        'code': c.code or '',
        'level': c.level,
        'has_children': c.children.exists(),
    } for c in categories]
    
    return JsonResponse({
        'categories': data,
        'count': len(data)
    })


@require_GET
@public_rate_limit(requests_per_minute=60)
def public_api_search_voters(request):
    """
    Public autocomplete search API endpoint.
    More restrictive than authenticated version.
    """
    query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 10)), 20)  # Max 20 results for public
    
    if len(query) < 2:
        return JsonResponse({'voters': [], 'count': 0, 'query': query})
    
    if query.isdigit():
        voters = Voter.objects.filter(
            Q(voter_no__icontains=query)
        ).select_related('category').annotate(
            relevance=Case(
                When(voter_no__exact=query, then=Value(100)),
                When(voter_no__startswith=query, then=Value(90)),
                When(voter_no__icontains=query, then=Value(70)),
                default=Value(50),
                output_field=IntegerField()
            )
        ).order_by('-relevance', 'voter_no')[:limit]
    else:
        voters = Voter.objects.filter(
            Q(name__icontains=query) |
            Q(father__icontains=query) |
            Q(mother__icontains=query) |
            Q(voter_no__icontains=query)
        ).select_related('category').annotate(
            relevance=Case(
                When(name__iexact=query, then=Value(100)),
                When(name__istartswith=query, then=Value(90)),
                When(name__icontains=query, then=Value(80)),
                When(voter_no__icontains=query, then=Value(75)),
                When(father__istartswith=query, then=Value(70)),
                When(mother__istartswith=query, then=Value(70)),
                default=Value(40),
                output_field=IntegerField()
            )
        ).order_by('-relevance', 'name')[:limit]
    
    results = []
    for v in voters:
        result = {
            'id': v.id,
            'serial': v.serial or '',
            'name': v.name or '',
            'voter_no': v.voter_no or '',
            'father': v.father or '',
            'mother': v.mother or '',
            'gender': v.gender,
            'address': v.address or '',
            'category': v.category.name if v.category else '',
            'name_highlighted': highlight_match(v.name or '', query),
            'voter_no_highlighted': highlight_match(v.voter_no or '', query),
        }
        results.append(result)
    
    return JsonResponse({
        'voters': results,
        'count': len(results),
        'query': query,
        'has_more': len(results) == limit
    })


@require_GET
@public_rate_limit(requests_per_minute=60)
def public_api_suggestions(request):
    """
    Public field-specific autocomplete suggestions endpoint.
    """
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'name').strip().lower()
    limit = min(int(request.GET.get('limit', 10)), 10)
    
    upazila_id = request.GET.get('upazila', '').strip()
    union_id = request.GET.get('union', '').strip()
    voter_area_id = request.GET.get('voter_area', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    allowed_fields = ['name', 'father', 'mother', 'address']
    if field not in allowed_fields:
        field = 'name'
    
    voters = Voter.objects.all()
    
    if voter_area_id:
        voters = voters.filter(category_id=voter_area_id)
    elif union_id:
        union_category = Category.objects.filter(id=union_id).first()
        if union_category:
            child_ids = list(union_category.children.values_list('id', flat=True))
            child_ids.append(int(union_id))
            voters = voters.filter(category_id__in=child_ids)
    elif upazila_id:
        upazila_category = Category.objects.filter(id=upazila_id).first()
        if upazila_category:
            union_ids = list(upazila_category.children.values_list('id', flat=True))
            voter_area_ids = list(Category.objects.filter(parent_id__in=union_ids).values_list('id', flat=True))
            all_ids = union_ids + voter_area_ids + [int(upazila_id)]
            voters = voters.filter(category_id__in=all_ids)
    
    field_filter = {f'{field}__icontains': query}
    voters = voters.filter(**field_filter)
    
    unique_values = voters.values_list(field, flat=True).distinct()[:limit * 2]
    
    seen = set()
    suggestions = []
    for value in unique_values:
        if value and value.strip():
            value_lower = value.lower()
            if value_lower not in seen:
                seen.add(value_lower)
                suggestions.append({
                    'text': value.strip(),
                    'field': field
                })
                if len(suggestions) >= limit:
                    break
    
    query_lower = query.lower()
    suggestions.sort(key=lambda x: (
        0 if x['text'].lower().startswith(query_lower) else 1,
        x['text'].lower()
    ))
    
    return JsonResponse({
        'suggestions': suggestions,
        'field': field,
        'query': query,
        'count': len(suggestions)
    })


@require_GET
def public_voter_slip(request, pk):
    """
    Get voter details for slip generation.
    Returns JSON data for client-side PDF/image generation.
    """
    voter = get_object_or_404(Voter.objects.select_related('category'), pk=pk)
    
    data = {
        'id': voter.id,
        'serial': voter.serial or '-',
        'name': voter.name or '-',
        'voter_no': voter.voter_no or '-',
        'father': voter.father or '-',
        'mother': voter.mother or '-',
        'gender': voter.get_gender_display() if voter.gender else '-',
        'dob': voter.dob or '-',
        'address': voter.address or '-',
        'category': voter.category.full_path if voter.category else '-',
    }
    
    return JsonResponse(data)


def highlight_match(text, query):
    """Add highlight markers around matched text"""
    if not text or not query:
        return escape(text or '')
    
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<mark>{escape(m.group())}</mark>', escape(text))
    return highlighted

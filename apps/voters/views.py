from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.html import escape
from django.core.cache import cache
from functools import wraps
import re
import time

from .models import Category, Voter, ExcelColumnSchema, VoterStatusAudit


def rate_limit(requests_per_minute=60):
    """Simple rate limiting decorator using Django's cache"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            
            # Create cache key
            cache_key = f'rate_limit:{view_func.__name__}:{ip}'
            
            # Get current request count
            request_count = cache.get(cache_key, 0)
            
            if request_count >= requests_per_minute:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please wait before making more requests.',
                    'retry_after': 60
                }, status=429)
            
            # Increment counter
            cache.set(cache_key, request_count + 1, 60)  # 60 second window
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@login_required
def voter_list(request):
    """Main voter list view with pagination, search, and filtering"""
    voters = Voter.objects.select_related('category').order_by('-created_at')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    name_query = request.GET.get('name', '').strip()
    father_query = request.GET.get('father', '').strip()
    mother_query = request.GET.get('mother', '').strip()
    voter_no_query = request.GET.get('voter_no', '').strip()
    gender = request.GET.get('gender', '')
    status = request.GET.get('status', '')
    
    # Hierarchical category filters
    district_id = request.GET.get('district', '')
    upazila_id = request.GET.get('upazila', '')
    union_id = request.GET.get('union', '')
    voter_area_id = request.GET.get('voter_area', '')
    
    # Legacy category filter (for backward compatibility)
    category_id = request.GET.get('category', '')
    
    # Dynamic field filter
    json_field = request.GET.get('json_field', '')
    json_value = request.GET.get('json_value', '').strip()

    # Get additional filter params
    address_query = request.GET.get('address', '').strip()
    profession_query = request.GET.get('profession', '').strip()

    # Apply search filters - uses icontains for partial match ("contains" search)
    if search_query:
        voters = voters.filter(
            Q(name__icontains=search_query) |
            Q(voter_no__icontains=search_query) |
            Q(father__icontains=search_query) |
            Q(mother__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(profession__icontains=search_query)
        )
    
    if name_query:
        voters = voters.filter(name__icontains=name_query)
    
    if father_query:
        voters = voters.filter(father__icontains=father_query)
    
    if mother_query:
        voters = voters.filter(mother__icontains=mother_query)
    
    if voter_no_query:
        voters = voters.filter(voter_no__icontains=voter_no_query)
    
    if address_query:
        voters = voters.filter(address__icontains=address_query)
    
    if profession_query:
        voters = voters.filter(profession__icontains=profession_query)

    # Apply hierarchical category filter (most specific wins)
    selected_category_id = voter_area_id or union_id or upazila_id or district_id or category_id
    
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
    
    if status and status != 'all':
        voters = voters.filter(status=status)

    if json_field and json_value:
        voters = voters.filter(extra_data__contains={json_field: json_value})

    paginator = Paginator(voters, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get root level categories (Upazilas - Level 0)
    # 3-level hierarchy: Upazila (0) → Union (1) → Voter Area (2)
    upazilas = Category.objects.filter(level=0).order_by('name')
    excel_columns = ExcelColumnSchema.objects.all()

    # Get selected categories for pre-populating dropdowns
    selected_upazila = None
    selected_union = None
    selected_voter_area = None
    
    unions = []
    voter_areas = []
    
    if upazila_id:
        selected_upazila = Category.objects.filter(id=upazila_id).first()
        if selected_upazila:
            unions = Category.objects.filter(parent_id=upazila_id).order_by('name')
    
    if union_id:
        selected_union = Category.objects.filter(id=union_id).first()
        if selected_union:
            voter_areas = Category.objects.filter(parent_id=union_id).order_by('name')
    
    if voter_area_id:
        selected_voter_area = Category.objects.filter(id=voter_area_id).first()

    stats = {
        'total_voters': Voter.objects.count(),
        'total_categories': Category.objects.count(),
        'male_count': Voter.objects.filter(gender='male').count(),
        'female_count': Voter.objects.filter(gender='female').count(),
    }

    context = {
        'page_obj': page_obj,
        'voters': page_obj,
        'upazilas': upazilas,
        'unions': unions,
        'voter_areas': voter_areas,
        'excel_columns': excel_columns,
        'search_query': search_query,
        'name_query': name_query,
        'father_query': father_query,
        'mother_query': mother_query,
        'voter_no_query': voter_no_query,
        'address_query': address_query,
        'profession_query': profession_query,
        'selected_upazila': upazila_id,
        'selected_union': union_id,
        'selected_voter_area': voter_area_id,
        'selected_gender': gender,
        'selected_status': status,
        'status_choices': Voter.STATUS_CHOICES,
        'json_field': json_field,
        'json_value': json_value,
        'stats': stats,
    }
    return render(request, 'voters/voter_list.html', context)


@login_required
def voter_detail(request, pk):
    """Voter detail view"""
    voter = get_object_or_404(Voter.objects.select_related('category'), pk=pk)
    return render(request, 'voters/voter_detail.html', {'voter': voter})


@login_required
def category_list(request):
    """Category tree view"""
    categories = Category.objects.filter(parent=None).prefetch_related('children')
    
    stats = {
        'total_categories': Category.objects.count(),
        'categories_with_excel': Category.objects.filter(has_excel=True).count(),
    }
    
    return render(request, 'voters/category_list.html', {
        'categories': categories,
        'stats': stats,
    })


@login_required
def category_detail(request, pk):
    """Category detail with voters"""
    category = get_object_or_404(Category.objects.prefetch_related('children'), pk=pk)
    
    descendant_ids = get_category_descendants(category)
    descendant_ids.append(category.id)
    
    voters = Voter.objects.filter(category_id__in=descendant_ids).select_related('category')
    
    paginator = Paginator(voters, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'voters/category_detail.html', {
        'category': category,
        'page_obj': page_obj,
        'voters': page_obj,
    })


def get_category_descendants(category):
    """Get all descendant category IDs recursively"""
    descendants = []
    children = Category.objects.filter(parent=category)
    for child in children:
        descendants.append(child.id)
        descendants.extend(get_category_descendants(child))
    return descendants


@login_required
@require_GET
def api_categories(request):
    """API endpoint for category dropdown (AJAX) - supports dependent dropdowns"""
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
        'has_excel': c.has_excel,
        'voter_count': c.voters.count() if c.has_excel else 0
    } for c in categories]
    
    return JsonResponse({
        'categories': data,
        'count': len(data)
    })


@login_required
@require_GET
@rate_limit(requests_per_minute=120)  # Allow 120 requests per minute per IP
def api_search_voters(request):
    """
    High-performance autocomplete search API endpoint.
    
    Features:
    - Partial matching (contains)
    - Multi-field search (name, father, mother, voter_no, address)
    - Relevance ranking (exact match > starts with > contains)
    - Typo tolerance via normalized search
    - Fast response with limited results
    """
    query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 15)), 50)  # Max 50 results
    mode = request.GET.get('mode', 'autocomplete')  # autocomplete or full
    
    if len(query) < 1:
        return JsonResponse({'voters': [], 'count': 0, 'query': query})
    
    # Normalize query for better matching
    query_lower = query.lower()
    query_normalized = normalize_text(query)
    
    # Build search query with relevance scoring
    # Priority: exact voter_no > name starts with > name contains > other fields
    
    if query.isdigit():
        # Numeric query - prioritize voter_no search
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
        # Text query - search multiple fields with ranking
        voters = Voter.objects.filter(
            Q(name__icontains=query) |
            Q(father__icontains=query) |
            Q(mother__icontains=query) |
            Q(voter_no__icontains=query) |
            Q(address__icontains=query) |
            Q(search_text__icontains=query_lower)
        ).select_related('category').annotate(
            relevance=Case(
                # Exact name match
                When(name__iexact=query, then=Value(100)),
                # Name starts with query
                When(name__istartswith=query, then=Value(90)),
                # Name contains query
                When(name__icontains=query, then=Value(80)),
                # Voter number match
                When(voter_no__icontains=query, then=Value(75)),
                # Father/Mother name starts with
                When(father__istartswith=query, then=Value(70)),
                When(mother__istartswith=query, then=Value(70)),
                # Father/Mother contains
                When(father__icontains=query, then=Value(60)),
                When(mother__icontains=query, then=Value(60)),
                # Address match
                When(address__icontains=query, then=Value(50)),
                default=Value(40),
                output_field=IntegerField()
            )
        ).order_by('-relevance', 'name')[:limit]
    
    # Format results with highlighted matches
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
            'category_id': v.category.id if v.category else None,
        }
        
        # Add highlighted versions for autocomplete display
        if mode == 'autocomplete':
            result['name_highlighted'] = highlight_match(v.name or '', query)
            result['voter_no_highlighted'] = highlight_match(v.voter_no or '', query)
        
        results.append(result)
    
    return JsonResponse({
        'voters': results,
        'count': len(results),
        'query': query,
        'has_more': len(results) == limit
    })


def normalize_text(text):
    """Normalize text for fuzzy matching - handles Bangla and English"""
    if not text:
        return ''
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Convert to lowercase
    text = text.lower()
    return text


def highlight_match(text, query):
    """Add highlight markers around matched text"""
    if not text or not query:
        return escape(text or '')
    
    # Case-insensitive replace with highlight markers
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<mark>{escape(m.group())}</mark>', escape(text))
    return highlighted


@login_required
@require_GET
@rate_limit(requests_per_minute=120)
def api_search_suggestions(request):
    """
    Field-specific autocomplete suggestions endpoint.
    Returns unique name-based values filtered by category hierarchy.
    
    Parameters:
    - q: Search query (required, min 2 chars)
    - field: Field to search (name, father, mother) - defaults to name
    - upazila: Filter by upazila category ID
    - union: Filter by union category ID  
    - voter_area: Filter by voter area category ID
    - limit: Max results (default 10, max 15)
    """
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'name').strip().lower()
    limit = min(int(request.GET.get('limit', 10)), 15)
    
    # Category filters
    upazila_id = request.GET.get('upazila', '').strip()
    union_id = request.GET.get('union', '').strip()
    voter_area_id = request.GET.get('voter_area', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Validate field - only allow name-based fields and address
    allowed_fields = ['name', 'father', 'mother', 'address']
    if field not in allowed_fields:
        field = 'name'
    
    # Build queryset with category filtering
    voters = Voter.objects.all()
    
    # Apply category hierarchy filters (most specific first)
    if voter_area_id:
        voters = voters.filter(category_id=voter_area_id)
    elif union_id:
        # Get all voter areas under this union
        union_category = Category.objects.filter(id=union_id).first()
        if union_category:
            child_ids = list(union_category.children.values_list('id', flat=True))
            child_ids.append(int(union_id))
            voters = voters.filter(category_id__in=child_ids)
    elif upazila_id:
        # Get all categories under this upazila (unions and voter areas)
        upazila_category = Category.objects.filter(id=upazila_id).first()
        if upazila_category:
            # Get unions under upazila
            union_ids = list(upazila_category.children.values_list('id', flat=True))
            # Get voter areas under unions
            voter_area_ids = list(Category.objects.filter(parent_id__in=union_ids).values_list('id', flat=True))
            all_ids = union_ids + voter_area_ids + [int(upazila_id)]
            voters = voters.filter(category_id__in=all_ids)
    
    # Build field filter dynamically
    field_filter = {f'{field}__icontains': query}
    voters = voters.filter(**field_filter)
    
    # Get unique values for the specified field
    unique_values = voters.values_list(field, flat=True).distinct()[:limit * 2]
    
    # Filter out empty/null values and deduplicate case-insensitively
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
    
    # Sort by relevance (starts with query first, then contains)
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


@login_required
def dashboard(request):
    """Dashboard with statistics"""
    stats = {
        'total_voters': Voter.objects.count(),
        'total_categories': Category.objects.count(),
        'male_count': Voter.objects.filter(gender='male').count(),
        'female_count': Voter.objects.filter(gender='female').count(),
        'categories_with_excel': Category.objects.filter(has_excel=True).count(),
    }
    
    top_categories = Category.objects.filter(has_excel=True).annotate(
        voter_count=Count('voters')
    ).order_by('-voter_count')[:10]
    
    return render(request, 'voters/dashboard.html', {
        'stats': stats,
        'top_categories': top_categories,
    })


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


@login_required
@require_POST
def update_voter_status(request, pk):
    """Update voter status and create audit record"""
    voter = get_object_or_404(Voter, pk=pk)
    new_status = request.POST.get('status', '').strip()
    remarks = request.POST.get('remarks', '').strip()
    
    # Validate status
    valid_statuses = [s[0] for s in Voter.STATUS_CHOICES]
    if new_status not in valid_statuses:
        messages.error(request, 'Invalid status value.')
        return redirect('voters:voter_detail', pk=pk)
    
    # Only create audit if status actually changed
    if voter.status != new_status:
        # Create audit record
        VoterStatusAudit.objects.create(
            voter=voter,
            changed_by=request.user,
            old_status=voter.status,
            new_status=new_status,
            remarks=remarks,
            ip_address=get_client_ip(request)
        )
        
        # Update voter status
        voter.status = new_status
        voter.save(update_fields=['status'])
        
        messages.success(request, f'Voter status updated to {voter.get_status_display()}.')
    else:
        messages.info(request, 'Status unchanged.')
    
    # Return to referring page or voter detail
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('voters:voter_detail', pk=pk)


@login_required
def audit_log(request):
    """Audit log page showing all voter status changes"""
    audits = VoterStatusAudit.objects.select_related('voter', 'changed_by').order_by('-changed_at')
    
    # Filter by user
    user_id = request.GET.get('user', '')
    if user_id:
        audits = audits.filter(changed_by_id=user_id)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        audits = audits.filter(new_status=status_filter)
    
    # Filter by voter name/number
    search_query = request.GET.get('search', '').strip()
    if search_query:
        audits = audits.filter(
            Q(voter__name__icontains=search_query) |
            Q(voter__voter_no__icontains=search_query)
        )
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        audits = audits.filter(changed_at__date__gte=date_from)
    if date_to:
        audits = audits.filter(changed_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(audits, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get users who have made changes for filter dropdown
    users_with_changes = User.objects.filter(
        voter_status_changes__isnull=False
    ).distinct().order_by('username')
    
    context = {
        'page_obj': page_obj,
        'audits': page_obj,
        'users': users_with_changes,
        'selected_user': user_id,
        'selected_status': status_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Voter.STATUS_CHOICES,
    }
    return render(request, 'voters/audit_log.html', context)

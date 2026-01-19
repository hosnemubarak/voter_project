from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages


@login_required
def dashboard(request):
    """Main dashboard view."""
    context = {
        'user': request.user,
    }
    return render(request, 'core/dashboard.html', context)


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        errors = []
        
        # Validation
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        if not password1:
            errors.append('Password is required.')
        elif len(password1) < 8:
            errors.append('Password must be at least 8 characters.')
        elif password1 != password2:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'core/register.html', {
                'form': {
                    'username': {'value': username},
                    'email': {'value': email},
                    'first_name': {'value': first_name},
                    'last_name': {'value': last_name},
                }
            })
        
        # Create user (inactive until admin approves)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        user.is_active = False
        user.save()
        
        messages.success(request, 'Your account has been created successfully! Please wait for admin approval before you can login.')
        return redirect('login')
    
    return render(request, 'core/register.html')


def error_400(request, exception=None):
    """Custom 400 Bad Request error page."""
    return render(request, '400.html', status=400)


def error_404(request, exception=None):
    """Custom 404 Not Found error page."""
    return render(request, '404.html', status=404)


def error_500(request):
    """Custom 500 Internal Server Error page."""
    return render(request, '500.html', status=500)

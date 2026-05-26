"""
Accounts Views — Admin authentication.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from elections.models import Election
from students.models import Student
from voting.models import VoterParticipation
from audit.services import log_action_from_request


def admin_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            log_action_from_request(request, f'Admin login: {username}', 'User', user.pk)
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')

    return render(request, 'admin_panel/login.html')


@login_required
def admin_logout(request):
    log_action_from_request(request, f'Admin logout: {request.user.username}')
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    elections = Election.objects.all()
    active_elections = elections.filter(status='active')
    closed_elections = elections.filter(status='closed')
    total_students = Student.objects.filter(status='active').count()
    total_votes = VoterParticipation.objects.filter(has_voted=True).count()
    eligible_voters = VoterParticipation.objects.count()
    recent_elections = elections[:5]

    # Per-election stats for active elections
    election_stats = []
    for election in active_elections:
        election_stats.append({
            'election': election,
            'eligible': election.total_eligible_voters,
            'voted': election.total_votes_cast,
            'turnout': election.voter_turnout_percentage,
        })

    context = {
        'total_elections': elections.count(),
        'active_elections_count': active_elections.count(),
        'closed_elections_count': closed_elections.count(),
        'total_students': total_students,
        'total_votes': total_votes,
        'eligible_voters': eligible_voters,
        'election_stats': election_stats,
        'recent_elections': recent_elections,
    }
    return render(request, 'admin_panel/dashboard.html', context)

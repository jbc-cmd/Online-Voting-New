"""
Analytics Views — Dashboard metrics, charts data, and detailed stats.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q

from elections.models import Election, Position
from students.models import Department, Program, ClassGroup
from voting.models import VoterParticipation, Vote, Ballot
from audit.models import VerificationLog


@login_required
def analytics_dashboard(request):
    elections = Election.objects.all()
    selected_election_pk = request.GET.get('election')

    if selected_election_pk:
        selected_election = get_object_or_404(Election, pk=selected_election_pk)
    else:
        selected_election = elections.filter(status='active').first() or elections.first()

    if selected_election:
        stats = _get_election_stats(selected_election)
    else:
        stats = {}

    return render(request, 'admin_panel/analytics/dashboard.html', {
        'elections': elections,
        'selected_election': selected_election,
        'stats': stats,
    })


@login_required
def analytics_data(request, pk):
    """JSON endpoint for Chart.js data."""
    election = get_object_or_404(Election, pk=pk)
    chart_type = request.GET.get('type', 'turnout')

    if chart_type == 'turnout_by_department':
        data = _turnout_by_department(election)
    elif chart_type == 'turnout_by_program':
        data = _turnout_by_program(election)
    elif chart_type == 'votes_by_candidate':
        data = _votes_by_candidate(election)
    elif chart_type == 'turnout_overview':
        total = election.total_eligible_voters
        voted = election.total_votes_cast
        not_voted = total - voted
        data = {
            'labels': ['Voted', 'Not Voted'],
            'datasets': [{
                'data': [voted, not_voted],
                'backgroundColor': ['#22c55e', '#ef4444'],
            }]
        }
    else:
        data = {}

    return JsonResponse(data)


def _get_election_stats(election: Election) -> dict:
    total_eligible = election.total_eligible_voters
    total_voted = election.total_votes_cast
    not_voted = total_eligible - total_voted
    turnout = election.voter_turnout_percentage

    # Duplicate attempts
    duplicate_count = VerificationLog.objects.filter(
        election=election, status='duplicate_attempt'
    ).count()

    # Failed verifications
    failed_count = VerificationLog.objects.filter(
        election=election
    ).exclude(status='success').count()

    # OTP stats
    from voting.models import OTPVerification
    otp_total = OTPVerification.objects.filter(election=election).count()
    otp_success = OTPVerification.objects.filter(election=election, status='verified').count()
    otp_failure = otp_total - otp_success

    # Votes per position
    position_stats = []
    for position in election.positions.prefetch_related('candidates').all():
        candidates_data = []
        for candidate in position.candidates.all():
            vc = Vote.objects.filter(
                candidate=candidate, election=election, is_abstain=False
            ).count()
            candidates_data.append({'candidate': candidate, 'votes': vc})
        abstain = Vote.objects.filter(position=position, election=election, is_abstain=True).count()
        candidates_data.sort(key=lambda x: x['votes'], reverse=True)
        position_stats.append({
            'position': position,
            'candidates': candidates_data,
            'abstain_count': abstain,
        })

    # Turnout by department
    dept_stats = _turnout_by_department(election)

    return {
        'total_eligible': total_eligible,
        'total_voted': total_voted,
        'not_voted': not_voted,
        'turnout': turnout,
        'duplicate_count': duplicate_count,
        'failed_count': failed_count,
        'otp_total': otp_total,
        'otp_success': otp_success,
        'otp_failure': otp_failure,
        'position_stats': position_stats,
        'dept_stats': dept_stats,
    }


def _turnout_by_department(election: Election) -> dict:
    departments = Department.objects.all()
    labels = []
    voted_data = []
    eligible_data = []

    for dept in departments:
        eligible = VoterParticipation.objects.filter(
            election=election, student__department=dept
        ).count()
        voted = VoterParticipation.objects.filter(
            election=election, student__department=dept, has_voted=True
        ).count()
        if eligible > 0:
            labels.append(dept.code)
            voted_data.append(voted)
            eligible_data.append(eligible)

    return {
        'labels': labels,
        'datasets': [
            {'label': 'Voted', 'data': voted_data, 'backgroundColor': '#22c55e'},
            {'label': 'Eligible', 'data': eligible_data, 'backgroundColor': '#3b82f6'},
        ]
    }


def _turnout_by_program(election: Election) -> dict:
    programs = Program.objects.all()
    labels = []
    voted_data = []

    for prog in programs:
        voted = VoterParticipation.objects.filter(
            election=election, student__program=prog, has_voted=True
        ).count()
        eligible = VoterParticipation.objects.filter(
            election=election, student__program=prog
        ).count()
        if eligible > 0:
            labels.append(prog.code)
            voted_data.append(voted)

    return {'labels': labels, 'datasets': [{'label': 'Votes Cast', 'data': voted_data, 'backgroundColor': '#8b5cf6'}]}


def _votes_by_candidate(election: Election) -> dict:
    positions = election.positions.prefetch_related('candidates').all()
    datasets = []
    for position in positions:
        labels = [c.name for c in position.candidates.all()]
        data = [
            Vote.objects.filter(candidate=c, is_abstain=False).count()
            for c in position.candidates.all()
        ]
        datasets.append({'position': position.title, 'labels': labels, 'data': data})
    return {'positions': datasets}

"""
Audit Views — Audit logs, verification logs, and system evaluation.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from audit.models import AuditLog, VerificationLog, SystemEvaluationReport
from elections.models import Election
from voting.models import OTPVerification, VoterParticipation


@login_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('actor').all()
    search = request.GET.get('search', '').strip()
    if search:
        logs = logs.filter(Q(action__icontains=search) | Q(actor__username__icontains=search))
    return render(request, 'admin_panel/audit_logs.html', {'logs': logs[:500], 'search': search})


@login_required
def verification_log_list(request):
    logs = VerificationLog.objects.select_related('election', 'student').all()
    election_filter = request.GET.get('election')
    status_filter = request.GET.get('status')

    if election_filter:
        logs = logs.filter(election_id=election_filter)
    if status_filter:
        logs = logs.filter(status=status_filter)

    elections = Election.objects.all()
    return render(request, 'admin_panel/verification_logs.html', {
        'logs': logs[:500],
        'elections': elections,
        'election_filter': election_filter,
        'status_filter': status_filter,
        'status_choices': VerificationLog.STATUS_CHOICES,
    })


@login_required
def system_evaluation(request):
    elections = Election.objects.all()
    selected_election_pk = request.GET.get('election')

    if selected_election_pk:
        election = get_object_or_404(Election, pk=selected_election_pk)
    else:
        election = elections.filter(status__in=['active', 'closed']).first()

    metrics = None
    if election:
        metrics = _compute_evaluation_metrics(election)

        if request.method == 'POST':
            # Save evaluation report
            SystemEvaluationReport.objects.create(
                election=election,
                vote_count_accuracy=metrics['accuracy'],
                successful_vote_submission_rate=metrics['success_rate'],
                failed_vote_attempt_rate=metrics['failure_rate'],
                duplicate_vote_prevention_count=metrics['duplicate_count'],
                otp_success_rate=metrics['otp_success_rate'],
                otp_failure_rate=metrics['otp_failure_rate'],
                usability_notes=request.POST.get('usability_notes', ''),
                reliability_notes=request.POST.get('reliability_notes', ''),
                security_notes=request.POST.get('security_notes', ''),
                performance_notes=request.POST.get('performance_notes', ''),
            )
            from django.contrib import messages
            messages.success(request, 'Evaluation report saved.')

    reports = SystemEvaluationReport.objects.select_related('election').all()[:10]
    return render(request, 'admin_panel/evaluation.html', {
        'elections': elections,
        'selected_election': election,
        'metrics': metrics,
        'reports': reports,
    })


def _compute_evaluation_metrics(election: Election) -> dict:
    total_eligible = election.total_eligible_voters
    total_voted = election.total_votes_cast

    # Verification logs
    all_verif = VerificationLog.objects.filter(election=election)
    total_verif = all_verif.count()
    success_verif = all_verif.filter(status='success').count()
    duplicate_count = all_verif.filter(status='duplicate_attempt').count()

    success_rate = round((total_voted / total_eligible * 100), 2) if total_eligible > 0 else 0
    failure_count = total_verif - success_verif
    failure_rate = round((failure_count / total_verif * 100), 2) if total_verif > 0 else 0

    # OTP stats
    otp_total = OTPVerification.objects.filter(election=election).count()
    otp_success = OTPVerification.objects.filter(election=election, status='verified').count()
    otp_success_rate = round((otp_success / otp_total * 100), 2) if otp_total > 0 else 0
    otp_failure_rate = round(((otp_total - otp_success) / otp_total * 100), 2) if otp_total > 0 else 0

    # Vote count accuracy: check ballot count == VoterParticipation count
    ballot_count = election.ballots.count()
    accuracy = 100.0 if ballot_count == total_voted else round((ballot_count / total_voted * 100), 2) if total_voted > 0 else 100.0

    return {
        'accuracy': accuracy,
        'success_rate': success_rate,
        'failure_rate': failure_rate,
        'duplicate_count': duplicate_count,
        'otp_success_rate': otp_success_rate,
        'otp_failure_rate': otp_failure_rate,
        'total_eligible': total_eligible,
        'total_voted': total_voted,
        'turnout': election.voter_turnout_percentage,
        'otp_total': otp_total,
        'otp_success': otp_success,
        'ballot_count': ballot_count,
    }

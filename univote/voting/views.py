"""
Voting Views — Google Form-style public voting flow.
No student login required. Session tracks verification state.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from elections.models import Election, Position
from students.models import Student
from voting.models import VoterParticipation, Ballot
from voting.services import (
    verify_student_credentials, send_otp, verify_otp,
    submit_ballot, get_ip
)


def _get_verified_student(request, election):
    """Return (student, error_response) from session."""
    student_pk = request.session.get(f'verified_student_{election.pk}')
    if not student_pk:
        return None, redirect('voting:credential_form', slug=election.slug)
    try:
        student = Student.objects.get(pk=student_pk)
    except Student.DoesNotExist:
        del request.session[f'verified_student_{election.pk}']
        return None, redirect('voting:credential_form', slug=election.slug)
    return student, None


# ─── Step 1: Credential Form ──────────────────────────────────────────────────

def credential_form(request, slug):
    """
    Landing page. Student enters Student ID + official email.
    """
    election = get_object_or_404(Election, slug=slug)

    if not election.is_voting_open():
        return render(request, 'voting/closed.html', {'election': election})

    if request.method == 'POST':
        student_id = request.POST.get('student_id_number', '').strip()
        email = request.POST.get('official_school_email', '').strip().lower()

        if not student_id or not email:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'voting/credential_form.html', {'election': election})

        result = verify_student_credentials(student_id, email, election, request)

        if result['error'] == 'election_closed':
            return render(request, 'voting/closed.html', {'election': election})

        if result['error'] == 'already_voted':
            return render(request, 'voting/already_voted.html', {'election': election})

        if result['error'] == 'not_eligible':
            return render(request, 'voting/not_eligible.html', {'election': election})

        if not result['success']:
            messages.error(request, 'Student ID and email do not match any official record. Please check your credentials.')
            return render(request, 'voting/credential_form.html', {'election': election})

        # Store student pk in session for OTP step
        student = result['student']
        request.session[f'pending_student_{election.pk}'] = student.pk
        request.session[f'pending_email_{election.pk}'] = email
        request.session.modified = True

        return redirect('voting:send_otp', slug=slug)

    return render(request, 'voting/credential_form.html', {'election': election})


# ─── Step 2: Send OTP ────────────────────────────────────────────────────────

def send_otp_view(request, slug):
    """Send OTP to student email and redirect to OTP form."""
    election = get_object_or_404(Election, slug=slug)
    if not election.is_voting_open():
        return render(request, 'voting/closed.html', {'election': election})

    student_pk = request.session.get(f'pending_student_{election.pk}')
    if not student_pk:
        return redirect('voting:credential_form', slug=slug)

    try:
        student = Student.objects.get(pk=student_pk)
    except Student.DoesNotExist:
        return redirect('voting:credential_form', slug=slug)

    result = send_otp(student, election)
    if not result['success']:
        messages.error(request, f'Failed to send OTP. Please try again.')
        return redirect('voting:credential_form', slug=slug)

    return redirect('voting:verify_otp', slug=slug)


# ─── Step 3: OTP Verification ────────────────────────────────────────────────

def verify_otp_view(request, slug):
    """Student enters the 6-digit OTP."""
    election = get_object_or_404(Election, slug=slug)
    if not election.is_voting_open():
        return render(request, 'voting/closed.html', {'election': election})

    student_pk = request.session.get(f'pending_student_{election.pk}')
    if not student_pk:
        return redirect('voting:credential_form', slug=slug)

    try:
        student = Student.objects.get(pk=student_pk)
    except Student.DoesNotExist:
        return redirect('voting:credential_form', slug=slug)

    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()
        result = verify_otp(student, election, otp_input, request)

        if result['success']:
            # Move to verified state
            request.session[f'verified_student_{election.pk}'] = student.pk
            # Clear pending
            request.session.pop(f'pending_student_{election.pk}', None)
            request.session.pop(f'pending_email_{election.pk}', None)
            request.session.modified = True
            return redirect('voting:ballot', slug=slug)

        error = result.get('error')
        if error == 'otp_expired':
            messages.error(request, 'Your OTP has expired. Please restart the verification process.')
            return redirect('voting:credential_form', slug=slug)
        elif error == 'otp_exhausted':
            messages.error(request, 'Too many failed attempts. Please restart the verification process.')
            return redirect('voting:credential_form', slug=slug)
        else:
            remaining = result.get('remaining', '')
            msg = f'Invalid OTP.'
            if remaining:
                msg += f' {remaining} attempt(s) remaining.'
            messages.error(request, msg)

    masked_email = _mask_email(student.official_school_email)
    return render(request, 'voting/verify_otp.html', {
        'election': election,
        'masked_email': masked_email,
    })


def resend_otp(request, slug):
    """Resend OTP (same as send_otp_view but POST only)."""
    election = get_object_or_404(Election, slug=slug)
    student_pk = request.session.get(f'pending_student_{election.pk}')
    if not student_pk:
        return redirect('voting:credential_form', slug=slug)
    try:
        student = Student.objects.get(pk=student_pk)
    except Student.DoesNotExist:
        return redirect('voting:credential_form', slug=slug)

    result = send_otp(student, election)
    if result['success']:
        messages.success(request, 'A new OTP has been sent to your email.')
    else:
        messages.error(request, 'Failed to resend OTP. Please try again.')
    return redirect('voting:verify_otp', slug=slug)


# ─── Step 4: Ballot ──────────────────────────────────────────────────────────

def ballot_view(request, slug):
    """Display ballot with positions and candidates."""
    election = get_object_or_404(Election, slug=slug)
    if not election.is_voting_open():
        return render(request, 'voting/closed.html', {'election': election})

    student, error_redirect = _get_verified_student(request, election)
    if error_redirect:
        return error_redirect

    # Double-check has not voted
    participation = VoterParticipation.objects.filter(election=election, student=student).first()
    if participation and participation.has_voted:
        return render(request, 'voting/already_voted.html', {'election': election})

    positions = election.positions.prefetch_related('candidates').all()
    return render(request, 'voting/ballot.html', {
        'election': election,
        'positions': positions,
        'student': student,
    })


# ─── Step 5: Review ──────────────────────────────────────────────────────────

def review_view(request, slug):
    """Show review page before final submission."""
    election = get_object_or_404(Election, slug=slug)
    if not election.is_voting_open():
        return render(request, 'voting/closed.html', {'election': election})

    student, error_redirect = _get_verified_student(request, election)
    if error_redirect:
        return error_redirect

    if request.method == 'POST':
        # Build selections dict from POST
        positions = election.positions.prefetch_related('candidates').all()
        selections = {}
        for position in positions:
            key = f'position_{position.pk}'
            values = request.POST.getlist(key)
            if values:
                selections[str(position.pk)] = values if len(values) > 1 else values[0]

        # Store selections in session for submit
        request.session[f'pending_ballot_{election.pk}'] = selections
        request.session.modified = True

        # Build review data
        review_items = _build_review_items(selections, positions, election)
        return render(request, 'voting/review.html', {
            'election': election,
            'review_items': review_items,
            'student': student,
        })

    return redirect('voting:ballot', slug=slug)


# ─── Step 6: Submit ──────────────────────────────────────────────────────────

def submit_view(request, slug):
    """Final atomic ballot submission."""
    election = get_object_or_404(Election, slug=slug)
    if not election.is_voting_open():
        return render(request, 'voting/closed.html', {'election': election})

    student, error_redirect = _get_verified_student(request, election)
    if error_redirect:
        return error_redirect

    if request.method != 'POST':
        return redirect('voting:ballot', slug=slug)

    selections = request.session.get(f'pending_ballot_{election.pk}')
    if not selections:
        messages.error(request, 'Your ballot data was lost. Please fill in your ballot again.')
        return redirect('voting:ballot', slug=slug)

    result = submit_ballot(student, election, selections, request)

    # Clear session data regardless
    for key in [f'verified_student_{election.pk}', f'pending_ballot_{election.pk}',
                f'pending_student_{election.pk}']:
        request.session.pop(key, None)
    request.session.modified = True

    if result['success']:
        return redirect('voting:receipt', slug=slug, ballot_number=result['ballot_number'])
    else:
        error = result.get('error', 'unknown')
        if error == 'already_voted':
            return render(request, 'voting/already_voted.html', {'election': election})
        elif error == 'election_closed':
            return render(request, 'voting/closed.html', {'election': election})
        else:
            messages.error(request, 'There was an error submitting your ballot. Please try again.')
            return redirect('voting:ballot', slug=slug)


# ─── Step 7: Receipt ─────────────────────────────────────────────────────────

def receipt_view(request, slug, ballot_number):
    """Show confirmation receipt with ballot number."""
    election = get_object_or_404(Election, slug=slug)
    ballot = get_object_or_404(Ballot, ballot_number=ballot_number, election=election)
    return render(request, 'voting/receipt.html', {
        'election': election,
        'ballot': ballot,
    })


# ─── Utility ─────────────────────────────────────────────────────────────────

def _mask_email(email: str) -> str:
    """Mask email for display: jo***@school.edu"""
    parts = email.split('@')
    if len(parts) != 2:
        return email
    local, domain = parts
    masked = local[:2] + '***' if len(local) > 2 else '***'
    return f"{masked}@{domain}"


def _build_review_items(selections: dict, positions, election) -> list:
    from elections.models import Candidate
    items = []
    for position in positions:
        sel = selections.get(str(position.pk))
        if not sel:
            items.append({'position': position, 'choice': 'No selection', 'is_abstain': False})
        elif sel == 'abstain' or sel == ['abstain']:
            items.append({'position': position, 'choice': 'Abstain', 'is_abstain': True})
        else:
            ids = sel if isinstance(sel, list) else [sel]
            candidates = Candidate.objects.filter(pk__in=ids, position=position)
            items.append({'position': position, 'candidates': list(candidates), 'is_abstain': False})
    return items

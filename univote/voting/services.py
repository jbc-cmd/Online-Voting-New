"""
Voting Services — Core business logic for the Univote voting flow.
All validation is done server-side. Never trust frontend-only data.
"""
import hashlib
import secrets
import string
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from elections.models import Election, ElectionEligibilityRule
from students.models import Student
from voting.models import OTPVerification, VoterParticipation, Ballot, Vote
from audit.services import log_verification


def get_ip(request):
    """Extract real IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:500]


# ─── Step 1: Verify student credentials ─────────────────────────────────────

def verify_student_credentials(student_id_number: str, election: Election, request) -> dict:
    """
    Check that the student_id_number matches an official active student record.
    Returns {'success': bool, 'student': Student|None, 'error': str}
    """
    ip = get_ip(request)
    ua = get_user_agent(request)
    attempted_email = ''

    # Check election is open
    if not election.is_voting_open():
        log_verification(election, None, student_id_number, attempted_email, 'election_closed',
                         'Election is not active', ip, ua)
        return {'success': False, 'student': None, 'error': 'election_closed'}

    # Look up student — check both fields together to prevent enumeration
    try:
        student = Student.objects.get(
            student_id_number__iexact=student_id_number.strip(),
            status='active'
        )
    except Student.DoesNotExist:
        log_verification(election, None, student_id_number, attempted_email, 'failed_not_found',
                         'Student not found', ip, ua)
        return {'success': False, 'student': None, 'error': 'invalid_credentials'}

    attempted_email = student.official_school_email

    # Check eligibility
    if not is_student_eligible(student, election):
        log_verification(election, student, student_id_number, attempted_email, 'failed_ineligible',
                         'Student not eligible for this election', ip, ua)
        return {'success': False, 'student': student, 'error': 'not_eligible'}

    # Check already voted
    participation = VoterParticipation.objects.filter(election=election, student=student).first()
    if participation and participation.has_voted:
        log_verification(election, student, student_id_number, attempted_email, 'failed_already_voted',
                         'Student has already voted', ip, ua)
        return {'success': False, 'student': student, 'error': 'already_voted'}

    # Ensure participation record exists (eligible voter)
    VoterParticipation.objects.get_or_create(election=election, student=student)

    log_verification(election, student, student_id_number, attempted_email, 'success',
                     'Credentials verified, OTP will be sent', ip, ua)
    return {'success': True, 'student': student, 'error': None}


# ─── Step 2: Send OTP ────────────────────────────────────────────────────────

def send_otp(student: Student, election: Election) -> dict:
    """
    Generate, hash, store, and email OTP.
    Returns {'success': bool, 'error': str}
    """
    # Expire any existing pending OTPs for this student+election
    OTPVerification.objects.filter(
        student=student, election=election, status='pending'
    ).update(status='expired')

    # Generate 6-digit OTP
    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
    otp_hash = OTPVerification.hash_otp(otp)
    expires_at = timezone.now() + timezone.timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    OTPVerification.objects.create(
        student=student,
        election=election,
        email=student.official_school_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
    )

    # ── Always print OTP to console (visible in dev server terminal) ──────────
    print("\n" + "=" * 60)
    print("  UNIVOTE OTP (Development Mode)")
    print("=" * 60)
    print(f"  Student : {student.first_name} {student.last_name}")
    print(f"  Email   : {student.official_school_email}")
    print(f"  OTP CODE: >>> {otp} <<<")
    print(f"  Expires : {settings.OTP_EXPIRY_MINUTES} minutes")
    print("=" * 60 + "\n")

    # Send email
    subject = f"Univote - Your OTP for {election.title}"
    message = (
        f"Hello {student.first_name},\n\n"
        f"Your one-time password (OTP) for the election:\n"
        f"  {election.title}\n\n"
        f"OTP: {otp}\n\n"
        f"This OTP expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
        f"Do not share this OTP with anyone.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"-- Univote System"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student.official_school_email])
        return {'success': True, 'error': None}
    except Exception as e:
        return {'success': False, 'error': str(e)}



# ─── Step 3: Verify OTP ──────────────────────────────────────────────────────

def verify_otp(student: Student, election: Election, otp_input: str, request) -> dict:
    """
    Verify the OTP entered by the student.
    Returns {'success': bool, 'error': str}
    """
    ip = get_ip(request)
    ua = get_user_agent(request)
    max_attempts = settings.OTP_MAX_ATTEMPTS

    otp_record = OTPVerification.objects.filter(
        student=student, election=election, status='pending'
    ).order_by('-created_at').first()

    if not otp_record:
        log_verification(election, student, student.student_id_number,
                         student.official_school_email, 'failed_otp_invalid',
                         'No pending OTP found', ip, ua)
        return {'success': False, 'error': 'otp_not_found'}

    if otp_record.is_expired():
        otp_record.status = 'expired'
        otp_record.save()
        log_verification(election, student, student.student_id_number,
                         student.official_school_email, 'failed_otp_expired',
                         'OTP has expired', ip, ua)
        return {'success': False, 'error': 'otp_expired'}

    otp_record.attempts += 1

    if otp_record.attempts >= max_attempts:
        otp_record.status = 'exhausted'
        otp_record.save()
        log_verification(election, student, student.student_id_number,
                         student.official_school_email, 'failed_otp_exhausted',
                         f'Max attempts ({max_attempts}) reached', ip, ua)
        return {'success': False, 'error': 'otp_exhausted'}

    input_hash = OTPVerification.hash_otp(otp_input.strip())
    if input_hash != otp_record.otp_hash:
        otp_record.save()
        log_verification(election, student, student.student_id_number,
                         student.official_school_email, 'failed_otp_invalid',
                         f'Invalid OTP (attempt {otp_record.attempts})', ip, ua)
        remaining = max_attempts - otp_record.attempts
        return {'success': False, 'error': 'otp_invalid', 'remaining': remaining}

    # OTP matched
    otp_record.status = 'verified'
    otp_record.verified_at = timezone.now()
    otp_record.save()

    log_verification(election, student, student.student_id_number,
                     student.official_school_email, 'success',
                     'OTP verified successfully', ip, ua)
    return {'success': True, 'error': None}


# ─── Step 4: Eligibility ─────────────────────────────────────────────────────

def is_student_eligible(student: Student, election: Election) -> bool:
    """
    Check if the student satisfies at least one eligibility rule.
    If no rules exist, USC elections allow all active students.
    """
    rules = election.eligibility_rules.all()

    if not rules.exists():
        # No rules = all active students eligible (typically USC)
        return election.election_type == 'usc'

    for rule in rules:
        if _student_matches_rule(student, rule):
            return True

    return False


def _student_matches_rule(student: Student, rule: ElectionEligibilityRule) -> bool:
    if rule.department and student.department != rule.department:
        return False
    if rule.program and student.program != rule.program:
        return False
    if rule.class_group and student.class_group != rule.class_group:
        return False
    if rule.organization and not student.organizations.filter(pk=rule.organization.pk).exists():
        return False
    if rule.year_level and student.year_level != rule.year_level:
        return False
    if rule.section and student.section != rule.section:
        return False
    return True


# ─── Step 5: Submit Ballot ───────────────────────────────────────────────────

def generate_ballot_number() -> str:
    """Generate a unique random ballot number."""
    while True:
        number = 'BLT-' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        if not Ballot.objects.filter(ballot_number=number).exists():
            return number


def generate_voter_hash(student: Student, election: Election) -> str:
    """Generate an anonymized voter hash (no PII linkable to vote choice)."""
    salt = secrets.token_hex(8)
    raw = f"{student.pk}-{election.pk}-{salt}"
    return hashlib.sha256(raw.encode()).hexdigest()


@transaction.atomic
def submit_ballot(student: Student, election: Election, selections: dict, request) -> dict:
    """
    Atomic ballot submission.
    selections = {position_id: [candidate_id, ...] or 'abstain'}
    Returns {'success': bool, 'ballot_number': str, 'error': str}
    """
    ip = get_ip(request)
    ua = get_user_agent(request)

    # ── Re-validate everything server-side ──────────────────────────────────
    if not election.is_voting_open():
        log_verification(election, student, student.student_id_number,
                         student.official_school_email, 'election_closed',
                         'Election not active at submit time', ip, ua)
        return {'success': False, 'error': 'election_closed'}

    # Lock VoterParticipation row with select_for_update to prevent races
    try:
        participation = VoterParticipation.objects.select_for_update().get(
            election=election, student=student
        )
    except VoterParticipation.DoesNotExist:
        return {'success': False, 'error': 'not_eligible'}

    if participation.has_voted:
        log_verification(election, student, student.student_id_number,
                         student.official_school_email, 'duplicate_attempt',
                         'Duplicate vote attempt at submit', ip, ua)
        return {'success': False, 'error': 'already_voted'}

    # Validate selections
    positions = election.positions.all()
    validation_error = _validate_selections(selections, positions, election.allow_abstain)
    if validation_error:
        return {'success': False, 'error': validation_error}

    # ── Create Ballot ────────────────────────────────────────────────────────
    ballot_number = generate_ballot_number()
    voter_hash = generate_voter_hash(student, election)
    ballot = Ballot.objects.create(
        election=election,
        ballot_number=ballot_number,
        anonymized_voter_hash=voter_hash,
    )

    # ── Record Votes ─────────────────────────────────────────────────────────
    for position in positions:
        pos_selection = selections.get(str(position.pk))
        if not pos_selection:
            continue

        if pos_selection == 'abstain' and election.allow_abstain:
            Vote.objects.create(
                ballot=ballot, election=election, position=position,
                candidate=None, is_abstain=True
            )
        else:
            candidate_ids = pos_selection if isinstance(pos_selection, list) else [pos_selection]
            # Validate count
            if len(candidate_ids) > position.max_choices:
                ballot.delete()
                return {'success': False, 'error': 'too_many_choices'}
            for candidate_id in candidate_ids:
                from elections.models import Candidate
                try:
                    candidate = Candidate.objects.get(
                        pk=candidate_id, position=position, election=election
                    )
                except Candidate.DoesNotExist:
                    ballot.delete()
                    return {'success': False, 'error': 'invalid_candidate'}
                Vote.objects.create(
                    ballot=ballot, election=election, position=position,
                    candidate=candidate, is_abstain=False
                )

    # ── Mark as Voted ─────────────────────────────────────────────────────────
    participation.has_voted = True
    participation.voted_at = timezone.now()
    participation.ballot_number = ballot_number
    participation.save()

    return {'success': True, 'ballot_number': ballot_number, 'error': None}


def _validate_selections(selections: dict, positions, allow_abstain: bool) -> str | None:
    """Validate selections dict against positions. Returns error string or None."""
    for position in positions:
        pos_selection = selections.get(str(position.pk))
        if not pos_selection:
            continue
        if pos_selection == 'abstain':
            if not allow_abstain:
                return 'abstain_not_allowed'
        else:
            ids = pos_selection if isinstance(pos_selection, list) else [pos_selection]
            if len(ids) > position.max_choices:
                return f'too_many_choices:{position.pk}'
    return None

"""
Elections Views — CRUD, toggle, positions, candidates.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings

from elections.models import Election, ElectionEligibilityRule, Position, Candidate
from students.models import Department, Program, ClassGroup, Organization
from audit.services import log_action_from_request
from voting.models import VoterParticipation
from students.models import Student


# ─── Elections CRUD ──────────────────────────────────────────────────────────

@login_required
def election_list(request):
    elections = Election.objects.select_related('created_by').all()
    return render(request, 'admin_panel/elections/list.html', {'elections': elections})


@login_required
def election_create(request):
    departments = Department.objects.all()
    programs = Program.objects.all()
    classes = ClassGroup.objects.all()
    organizations = Organization.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        election_type = request.POST.get('election_type')
        status = request.POST.get('status', 'draft')
        allow_abstain = request.POST.get('allow_abstain') == 'on'
        results_visibility = request.POST.get('results_visibility', 'admin_only')
        starts_at = request.POST.get('starts_at') or None
        ends_at = request.POST.get('ends_at') or None

        if not title or not election_type:
            messages.error(request, 'Title and election type are required.')
        else:
            election = Election.objects.create(
                title=title,
                description=description,
                election_type=election_type,
                status=status,
                is_active=(status == 'active'),
                allow_abstain=allow_abstain,
                results_visibility=results_visibility,
                starts_at=starts_at,
                ends_at=ends_at,
                created_by=request.user,
            )

            # Eligibility rules
            _save_eligibility_rules(election, request.POST)

            # Auto-populate eligible voters
            _populate_eligible_voters(election)

            log_action_from_request(request, f'Created election: {title}', 'Election', election.pk)
            messages.success(request, f'Election "{title}" created successfully!')
            return redirect('elections:election_edit', pk=election.pk)

    context = {
        'departments': departments, 'programs': programs,
        'classes': classes, 'organizations': organizations,
        'election_types': Election.ELECTION_TYPES,
        'status_choices': Election.STATUS_CHOICES,
    }
    return render(request, 'admin_panel/elections/create.html', context)


@login_required
def election_edit(request, pk):
    election = get_object_or_404(Election, pk=pk)
    departments = Department.objects.all()
    programs = Program.objects.all()
    classes = ClassGroup.objects.all()
    organizations = Organization.objects.all()

    if request.method == 'POST':
        election.title = request.POST.get('title', election.title).strip()
        election.description = request.POST.get('description', '').strip()
        election.election_type = request.POST.get('election_type', election.election_type)
        election.status = request.POST.get('status', election.status)
        election.is_active = election.status == 'active'
        election.allow_abstain = request.POST.get('allow_abstain') == 'on'
        election.results_visibility = request.POST.get('results_visibility', 'admin_only')
        starts = request.POST.get('starts_at')
        ends = request.POST.get('ends_at')
        election.starts_at = starts or None
        election.ends_at = ends or None
        election.save()

        election.eligibility_rules.all().delete()
        _save_eligibility_rules(election, request.POST)
        _populate_eligible_voters(election)

        log_action_from_request(request, f'Updated election: {election.title}', 'Election', pk)
        messages.success(request, 'Election updated successfully!')
        return redirect('elections:election_edit', pk=pk)

    current_rules = election.eligibility_rules.all()
    context = {
        'election': election, 'departments': departments, 'programs': programs,
        'classes': classes, 'organizations': organizations,
        'election_types': Election.ELECTION_TYPES,
        'status_choices': Election.STATUS_CHOICES,
        'current_rules': current_rules,
        'site_url': settings.SITE_URL,
    }
    return render(request, 'admin_panel/elections/edit.html', context)


@login_required
def election_delete(request, pk):
    election = get_object_or_404(Election, pk=pk)
    if request.method == 'POST':
        title = election.title
        election.delete()
        log_action_from_request(request, f'Deleted election: {title}', 'Election', pk)
        messages.success(request, f'Election "{title}" deleted.')
        return redirect('elections:election_list')
    return render(request, 'admin_panel/elections/delete_confirm.html', {'election': election})


@login_required
@require_POST
def election_toggle(request, pk):
    """AJAX toggle is_active."""
    election = get_object_or_404(Election, pk=pk)
    data = json.loads(request.body)
    new_state = data.get('is_active', not election.is_active)

    if new_state and election.status == 'closed':
        return JsonResponse({'success': False, 'error': 'Cannot activate a closed election.'})

    election.is_active = new_state
    if new_state and election.status in ('draft', 'paused'):
        election.status = 'active'
    elif not new_state and election.status == 'active':
        election.status = 'paused'
    election.save()

    action = 'activated' if new_state else 'paused'
    log_action_from_request(request, f'Election {action}: {election.title}', 'Election', pk)
    return JsonResponse({
        'success': True,
        'is_active': election.is_active,
        'status': election.status,
        'status_display': election.get_status_display(),
    })


# ─── Positions ───────────────────────────────────────────────────────────────

@login_required
def manage_positions(request, pk):
    election = get_object_or_404(Election, pk=pk)
    positions = election.positions.prefetch_related('candidates').all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            title = request.POST.get('title', '').strip()
            max_choices = int(request.POST.get('max_choices', 1))
            is_required = request.POST.get('is_required') == 'on'
            description = request.POST.get('description', '').strip()
            display_order = int(request.POST.get('display_order', 0))
            if title:
                Position.objects.create(
                    election=election, title=title, max_choices=max_choices,
                    is_required=is_required, description=description,
                    display_order=display_order,
                )
                messages.success(request, f'Position "{title}" added.')
                log_action_from_request(request, f'Added position: {title}', 'Position', election.pk)
        elif action == 'delete':
            pos_pk = request.POST.get('position_pk')
            Position.objects.filter(pk=pos_pk, election=election).delete()
            messages.success(request, 'Position deleted.')
        return redirect('elections:manage_positions', pk=pk)

    return render(request, 'admin_panel/elections/positions.html', {
        'election': election, 'positions': positions
    })


# ─── Candidates ──────────────────────────────────────────────────────────────

@login_required
def manage_candidates(request, pk):
    election = get_object_or_404(Election, pk=pk)
    positions = election.positions.prefetch_related('candidates').all()
    departments = Department.objects.all()
    programs = Program.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            position_pk = request.POST.get('position_pk')
            name = request.POST.get('name', '').strip()
            partylist = request.POST.get('partylist', '').strip()
            description = request.POST.get('description', '').strip()
            platform = request.POST.get('platform', '').strip()
            department_pk = request.POST.get('department') or None
            program_pk = request.POST.get('program') or None
            photo = request.FILES.get('photo')

            if name and position_pk:
                position = get_object_or_404(Position, pk=position_pk, election=election)
                Candidate.objects.create(
                    election=election, position=position, name=name,
                    partylist=partylist, description=description,
                    platform=platform,
                    department_id=department_pk,
                    program_id=program_pk,
                    photo=photo,
                )
                messages.success(request, f'Candidate "{name}" added.')
                log_action_from_request(request, f'Added candidate: {name}', 'Candidate', election.pk)
        elif action == 'delete':
            candidate_pk = request.POST.get('candidate_pk')
            Candidate.objects.filter(pk=candidate_pk, election=election).delete()
            messages.success(request, 'Candidate deleted.')
        return redirect('elections:manage_candidates', pk=pk)

    return render(request, 'admin_panel/elections/candidates.html', {
        'election': election, 'positions': positions,
        'departments': departments, 'programs': programs,
    })


@login_required
def election_results(request, pk):
    election = get_object_or_404(Election, pk=pk)
    positions = election.positions.prefetch_related('candidates').all()

    results = []
    for position in positions:
        from voting.models import Vote
        from django.db.models import Count
        candidates_data = []
        for candidate in position.candidates.all():
            vote_count = Vote.objects.filter(
                candidate=candidate, election=election, is_abstain=False
            ).count()
            candidates_data.append({'candidate': candidate, 'votes': vote_count})
        abstain_count = Vote.objects.filter(
            position=position, election=election, is_abstain=True
        ).count()
        candidates_data.sort(key=lambda x: x['votes'], reverse=True)
        results.append({
            'position': position,
            'candidates': candidates_data,
            'abstain_count': abstain_count,
        })

    context = {
        'election': election,
        'results': results,
        'total_eligible': election.total_eligible_voters,
        'total_voted': election.total_votes_cast,
        'turnout': election.voter_turnout_percentage,
    }
    return render(request, 'admin_panel/elections/results.html', context)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _save_eligibility_rules(election, post_data):
    department_ids = post_data.getlist('departments')
    program_ids = post_data.getlist('programs')
    class_ids = post_data.getlist('classes')
    org_ids = post_data.getlist('organizations')
    year_levels = post_data.getlist('year_levels')

    # If USC type and no specific rules, no rules needed (all students eligible)
    if election.election_type == 'usc' and not any([department_ids, program_ids, class_ids, org_ids]):
        return

    # Create rules per department if specified
    if department_ids:
        for dept_id in department_ids:
            ElectionEligibilityRule.objects.create(election=election, department_id=dept_id)
    if program_ids:
        for prog_id in program_ids:
            ElectionEligibilityRule.objects.create(election=election, program_id=prog_id)
    if class_ids:
        for class_id in class_ids:
            ElectionEligibilityRule.objects.create(election=election, class_group_id=class_id)
    if org_ids:
        for org_id in org_ids:
            ElectionEligibilityRule.objects.create(election=election, organization_id=org_id)
    if year_levels and not (department_ids or program_ids or class_ids):
        for yl in year_levels:
            ElectionEligibilityRule.objects.create(election=election, year_level=yl)


def _populate_eligible_voters(election):
    """
    Create VoterParticipation records for all eligible students.
    """
    from voting.services import is_student_eligible
    students = Student.objects.filter(status='active')
    for student in students:
        if is_student_eligible(student, election):
            VoterParticipation.objects.get_or_create(election=election, student=student)

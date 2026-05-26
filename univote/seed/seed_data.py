"""
Univote Seed Data Script
Run: python seed/seed_data.py
"""
import os
import sys
import django

# Setup Django - reads .env automatically via python-decouple
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
os.chdir(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'univote_config.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import AdminProfile
from students.models import Department, Program, ClassGroup, Organization, Student
from elections.models import Election, ElectionEligibilityRule, Position, Candidate
from voting.models import VoterParticipation
from voting.services import is_student_eligible

print("=" * 60)
print("  Univote Seed Data Generator")
print("=" * 60)


# --- Admin Users --------------------------------------------------------------

def create_admin(username, password, email, first_name, last_name, role='election_admin'):
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': email, 'first_name': first_name, 'last_name': last_name,
        'is_staff': True, 'is_active': True,
    })
    if created:
        user.set_password(password)
        user.save()
        AdminProfile.objects.create(
            user=user, role=role,
            is_super_admin=(role == 'super_admin')
        )
        print(f"  [OK] Admin created: {username} / {password}")
    else:
        print(f"  [--] Admin exists:  {username}")
    return user


print("\n[1] Creating admin users...")
super_admin = create_admin('superadmin', 'Admin@1234', 'superadmin@univote.edu',
                           'Super', 'Admin', 'super_admin')
admin1 = create_admin('admin_ccs', 'Admin@1234', 'admin_ccs@univote.edu',
                      'CCS', 'Admin', 'election_admin')
admin2 = create_admin('admin_cba', 'Admin@1234', 'admin_cba@univote.edu',
                      'CBA', 'Admin', 'election_admin')


# --- Departments --------------------------------------------------------------

print("\n[2] Creating departments...")
ccs, _ = Department.objects.get_or_create(code='CCS', defaults={'name': 'College of Computer Studies'})
cba, _ = Department.objects.get_or_create(code='CBA', defaults={'name': 'College of Business Administration'})
ced, _ = Department.objects.get_or_create(code='CED', defaults={'name': 'College of Education'})

for dept in [ccs, cba, ced]:
    print(f"  [OK] {dept.code}: {dept.name}")


# --- Programs -----------------------------------------------------------------

print("\n[3] Creating programs...")
bsit, _ = Program.objects.get_or_create(code='BSIT', defaults={'name': 'Bachelor of Science in Information Technology', 'department': ccs})
bscs, _ = Program.objects.get_or_create(code='BSCS', defaults={'name': 'Bachelor of Science in Computer Science', 'department': ccs})
bsba, _ = Program.objects.get_or_create(code='BSBA', defaults={'name': 'Bachelor of Science in Business Administration', 'department': cba})
bsed, _ = Program.objects.get_or_create(code='BSEd', defaults={'name': 'Bachelor of Secondary Education', 'department': ced})

for prog in [bsit, bscs, bsba, bsed]:
    print(f"  [OK] {prog.code}: {prog.name}")


# --- Classes ------------------------------------------------------------------

print("\n[4] Creating class groups...")
classes_data = [
    (bsit, '1', 'A', 'BSIT 1A'), (bsit, '2', 'A', 'BSIT 2A'),
    (bsit, '3', 'A', 'BSIT 3A'), (bscs, '2', 'A', 'BSCS 2A'),
    (bsba, '1', 'A', 'BSBA 1A'), (bsed, '2', 'A', 'BSEd 2A'),
]
class_objects = {}
for prog, year, section, name in classes_data:
    cls, _ = ClassGroup.objects.get_or_create(
        program=prog, year_level=year, section=section, defaults={'name': name}
    )
    class_objects[name] = cls
    print(f"  [OK] {name}")


# --- Organizations ------------------------------------------------------------

print("\n[5] Creating organizations...")
comp_soc, _ = Organization.objects.get_or_create(
    name='Computer Society', defaults={'description': 'Student organization for computing enthusiasts'}
)
bus_club, _ = Organization.objects.get_or_create(
    name='Business Club', defaults={'description': 'Student organization for business students'}
)
print(f"  [OK] {comp_soc.name}")
print(f"  [OK] {bus_club.name}")


# --- Students -----------------------------------------------------------------

print("\n[6] Creating students...")
students_data = [
    ('2024-0001', 'juan.delacruz@ccs.edu', 'Juan', 'Dela Cruz', ccs, bsit, '2', 'A', 'BSIT 2A'),
    ('2024-0002', 'maria.santos@ccs.edu', 'Maria', 'Santos', ccs, bsit, '2', 'A', 'BSIT 2A'),
    ('2024-0003', 'jose.reyes@ccs.edu', 'Jose', 'Reyes', ccs, bsit, '2', 'A', 'BSIT 2A'),
    ('2024-0004', 'ana.garcia@ccs.edu', 'Ana', 'Garcia', ccs, bsit, '2', 'A', 'BSIT 2A'),
    ('2024-0005', 'pedro.lim@ccs.edu', 'Pedro', 'Lim', ccs, bsit, '2', 'A', 'BSIT 2A'),
    ('2024-0006', 'carlo.mendoza@ccs.edu', 'Carlo', 'Mendoza', ccs, bsit, '1', 'A', 'BSIT 1A'),
    ('2024-0007', 'rosa.aquino@ccs.edu', 'Rosa', 'Aquino', ccs, bsit, '1', 'A', 'BSIT 1A'),
    ('2024-0008', 'marco.torres@ccs.edu', 'Marco', 'Torres', ccs, bscs, '2', 'A', 'BSCS 2A'),
    ('2024-0009', 'liza.flores@ccs.edu', 'Liza', 'Flores', ccs, bscs, '2', 'A', 'BSCS 2A'),
    ('2024-0010', 'antonio.ramos@cba.edu', 'Antonio', 'Ramos', cba, bsba, '1', 'A', 'BSBA 1A'),
    ('2024-0011', 'carmen.cruz@cba.edu', 'Carmen', 'Cruz', cba, bsba, '1', 'A', 'BSBA 1A'),
    ('2024-0012', 'julio.morales@cba.edu', 'Julio', 'Morales', cba, bsba, '1', 'A', 'BSBA 1A'),
    ('2024-0013', 'linda.pascual@ced.edu', 'Linda', 'Pascual', ced, bsed, '2', 'A', 'BSEd 2A'),
    ('2024-0014', 'mario.san@ced.edu', 'Mario', 'San', ced, bsed, '2', 'A', 'BSEd 2A'),
    ('2024-0015', 'teresa.bautista@ccs.edu', 'Teresa', 'Bautista', ccs, bsit, '3', 'A', 'BSIT 3A'),
    ('2024-0016', 'felix.castillo@ccs.edu', 'Felix', 'Castillo', ccs, bsit, '3', 'A', 'BSIT 3A'),
    ('2024-0017', 'grace.villanueva@ccs.edu', 'Grace', 'Villanueva', ccs, bsit, '3', 'A', 'BSIT 3A'),
    ('2024-0018', 'roberto.navarro@ccs.edu', 'Roberto', 'Navarro', ccs, bsit, '3', 'A', 'BSIT 3A'),
    ('2024-0019', 'elena.padilla@ccs.edu', 'Elena', 'Padilla', ccs, bsit, '3', 'A', 'BSIT 3A'),
    ('2024-0020', 'diego.herrera@ccs.edu', 'Diego', 'Herrera', ccs, bsit, '3', 'A', 'BSIT 3A'),
]

student_objects = []
for sid, email, first, last, dept, prog, year, section, cls_name in students_data:
    cls = class_objects.get(cls_name)
    student, created = Student.objects.get_or_create(
        student_id_number=sid,
        defaults={
            'official_school_email': email,
            'first_name': first, 'last_name': last,
            'department': dept, 'program': prog,
            'year_level': year, 'section': section,
            'class_group': cls, 'status': 'active',
        }
    )
    student_objects.append(student)
    if created:
        print(f"  [OK] {sid}: {first} {last} ({prog.code} {year}{section})")

for s in student_objects[:5]:
    s.organizations.add(comp_soc)
for s in student_objects[9:12]:
    s.organizations.add(bus_club)

print(f"  Total students: {len(student_objects)}")


# --- Elections ----------------------------------------------------------------

print("\n[7] Creating elections...")

usc, _ = Election.objects.get_or_create(
    slug='usc-election-2026',
    defaults={
        'title': 'USC Election 2026',
        'description': 'University Student Council Election for Academic Year 2026-2027. All active students are eligible to vote.',
        'election_type': 'usc',
        'status': 'active',
        'is_active': True,
        'allow_abstain': True,
        'results_visibility': 'admin_only',
        'created_by': super_admin,
    }
)
print(f"  [OK] {usc.title} (slug: {usc.slug})")

dept_election, _ = Election.objects.get_or_create(
    slug='ccs-department-election-2026',
    defaults={
        'title': 'College of Computer Studies Department Election 2026',
        'description': 'Department-level election for CCS students.',
        'election_type': 'department',
        'status': 'active',
        'is_active': True,
        'allow_abstain': False,
        'created_by': super_admin,
    }
)
if not dept_election.eligibility_rules.exists():
    ElectionEligibilityRule.objects.create(election=dept_election, department=ccs)
print(f"  [OK] {dept_election.title}")

prog_election, _ = Election.objects.get_or_create(
    slug='bsit-program-election-2026',
    defaults={
        'title': 'BSIT Program Election 2026',
        'description': 'Program election for BSIT students.',
        'election_type': 'program',
        'status': 'draft',
        'is_active': False,
        'allow_abstain': True,
        'created_by': admin1,
    }
)
if not prog_election.eligibility_rules.exists():
    ElectionEligibilityRule.objects.create(election=prog_election, program=bsit)
print(f"  [OK] {prog_election.title}")

org_election, _ = Election.objects.get_or_create(
    slug='computer-society-election-2026',
    defaults={
        'title': 'Computer Society Organization Election 2026',
        'description': 'Election for Computer Society members.',
        'election_type': 'organization',
        'status': 'draft',
        'is_active': False,
        'allow_abstain': False,
        'created_by': admin1,
    }
)
if not org_election.eligibility_rules.exists():
    ElectionEligibilityRule.objects.create(election=org_election, organization=comp_soc)
print(f"  [OK] {org_election.title}")

class_election, _ = Election.objects.get_or_create(
    slug='bsit-2a-class-election-2026',
    defaults={
        'title': 'BSIT 2A Class Election 2026',
        'description': 'Class-level election for BSIT 2A students.',
        'election_type': 'class',
        'status': 'draft',
        'is_active': False,
        'allow_abstain': False,
        'created_by': admin1,
    }
)
if not class_election.eligibility_rules.exists():
    ElectionEligibilityRule.objects.create(
        election=class_election, class_group=class_objects['BSIT 2A']
    )
print(f"  [OK] {class_election.title}")


# --- Positions & Candidates ---------------------------------------------------

def add_position(election, title, max_choices=1, is_required=True, display_order=0):
    pos, _ = Position.objects.get_or_create(
        election=election, title=title,
        defaults={'max_choices': max_choices, 'is_required': is_required, 'display_order': display_order}
    )
    return pos


def add_candidate(election, position, name, partylist='', description=''):
    cand, _ = Candidate.objects.get_or_create(
        election=election, position=position, name=name,
        defaults={'partylist': partylist, 'description': description}
    )
    return cand


print("\n[8] Creating positions and candidates...")

pres = add_position(usc, 'President', display_order=1)
vp   = add_position(usc, 'Vice President', display_order=2)
sec  = add_position(usc, 'Secretary', display_order=3)
tres = add_position(usc, 'Treasurer', display_order=4)
rep  = add_position(usc, 'Representative', max_choices=3, display_order=5)

add_candidate(usc, pres, 'Alejandro Reyes', 'Unity Party', 'Fighting for student rights')
add_candidate(usc, pres, 'Brigitte Lim', 'Progress Party', 'Academic excellence and welfare')
add_candidate(usc, vp,   'Carlos Mendoza', 'Unity Party', 'Student welfare advocate')
add_candidate(usc, vp,   'Daphne Santos', 'Progress Party', 'Inclusive leadership')
add_candidate(usc, sec,  'Emmanuel Torres', 'Unity Party')
add_candidate(usc, sec,  'Fiona Cruz', 'Progress Party')
add_candidate(usc, tres, 'Gonzalo Aquino', 'Unity Party')
add_candidate(usc, tres, 'Hannah Garcia', 'Progress Party')
add_candidate(usc, rep,  'Ignacio Flores', 'Unity Party')
add_candidate(usc, rep,  'Jessica Morales', 'Progress Party')
add_candidate(usc, rep,  'Kevin Villanueva', 'Unity Party')
add_candidate(usc, rep,  'Lena Castillo', 'Progress Party')
print("  [OK] USC Election: 5 positions, 12 candidates")

dept_pres = add_position(dept_election, 'Department President', display_order=1)
dept_vp   = add_position(dept_election, 'Department Vice President', display_order=2)
dept_sec  = add_position(dept_election, 'Department Secretary', display_order=3)
add_candidate(dept_election, dept_pres, 'Marco Torres', 'CCS Leaders', 'Tech for all')
add_candidate(dept_election, dept_pres, 'Nina Reyes', 'CCS Forward', 'Innovation first')
add_candidate(dept_election, dept_vp,   'Oscar Lim', 'CCS Leaders')
add_candidate(dept_election, dept_vp,   'Patricia Santos', 'CCS Forward')
add_candidate(dept_election, dept_sec,  'Quincy Dela Cruz', 'CCS Leaders')
add_candidate(dept_election, dept_sec,  'Rachel Navarro', 'CCS Forward')
print("  [OK] Department Election: 3 positions, 6 candidates")

prog_pres = add_position(prog_election, 'BSIT Governor', display_order=1)
prog_vp   = add_position(prog_election, 'BSIT Deputy Governor', display_order=2)
add_candidate(prog_election, prog_pres, 'Samuel Bautista', 'BSIT United')
add_candidate(prog_election, prog_pres, 'Tina Padilla', 'IT Scholars')
add_candidate(prog_election, prog_vp,   'Ulysses Herrera', 'BSIT United')
add_candidate(prog_election, prog_vp,   'Vera Castillo', 'IT Scholars')
print("  [OK] Program Election: 2 positions, 4 candidates")


# --- Populate Eligible Voters -------------------------------------------------

print("\n[9] Populating eligible voters...")
for election in [usc, dept_election, prog_election, org_election, class_election]:
    for student in student_objects:
        if is_student_eligible(student, election):
            VoterParticipation.objects.get_or_create(election=election, student=student)
    count = VoterParticipation.objects.filter(election=election).count()
    print(f"  [OK] {election.title}: {count} eligible voters")


print("\n" + "=" * 60)
print("  Seed data complete!")
print("=" * 60)
print("\nAdmin credentials:")
print("  Username: superadmin   Password: Admin@1234")
print("  Username: admin_ccs    Password: Admin@1234")
print("  Username: admin_cba    Password: Admin@1234")
print("\nVoting links:")
print("  /vote/usc-election-2026/")
print("  /vote/ccs-department-election-2026/")
print("\nSample student credentials:")
print("  Student ID: 2024-0001  Email: juan.delacruz@ccs.edu")
print("  Student ID: 2024-0002  Email: maria.santos@ccs.edu")
print("=" * 60)

import csv
from collections import defaultdict

def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

centers = load_csv("centers.csv")
students = load_csv("students.csv")
teachers = load_csv("teachers.csv")

for c in centers:
    c["capacity"] = int(c["capacity"])

# center capacity remaining tracker, grouped by city (a city can have multiple centers)
city_centers = defaultdict(list)
for c in centers:
    city_centers[c["city"]].append(c)

remaining = {c["center_id"]: c["capacity"] for c in centers}

def allocate_to_city(city, student):
    """Try to place a student in any center in given city with free capacity. Returns center_id or None."""
    for c in city_centers.get(city, []):
        if remaining[c["center_id"]] > 0:
            remaining[c["center_id"]] -= 1
            return c["center_id"]
    return None

# STEP 1: allocate girls first, home city (pref1) priority, to minimize their travel
girls = [s for s in students if s["gender"] == "F"]
boys = [s for s in students if s["gender"] == "M"]

allocation = {}
unallocated = []

def process_group(group, label):
    for s in group:
        center = allocate_to_city(s["pref1_city"], s)
        used_pref = "pref1"
        if center is None:
            center = allocate_to_city(s["pref2_city"], s)
            used_pref = "pref2"
        if center is None:
            unallocated.append(s)
            continue
        allocation[s["student_id"]] = {
            "student": s,
            "center_id": center,
            "assigned_via": used_pref,
        }

# Girls get priority pass first (their pref1 = home city, so this directly minimizes girl travel)
process_group(girls, "girls")
process_group(boys, "boys")

# STEP 2: Retry unallocated students against ANY center with space (last resort)
still_unallocated = []
for s in unallocated:
    placed = False
    for c in centers:
        if remaining[c["center_id"]] > 0:
            remaining[c["center_id"]] -= 1
            allocation[s["student_id"]] = {"student": s, "center_id": c["center_id"], "assigned_via": "overflow"}
            placed = True
            break
    if not placed:
        still_unallocated.append(s)

# ---------- Build results table ----------
center_by_id = {c["center_id"]: c for c in centers}
results = []
for sid, info in allocation.items():
    s = info["student"]
    c = center_by_id[info["center_id"]]
    same_city = (c["city"] == s["home_city"])
    results.append({
        "student_id": s["student_id"],
        "name": s["name"],
        "gender": s["gender"],
        "home_city": s["home_city"],
        "pref1_city": s["pref1_city"],
        "pref2_city": s["pref2_city"],
        "assigned_center": info["center_id"],
        "assigned_city": c["city"],
        "assigned_via": info["assigned_via"],
        "traveled_outside_home_city": "No" if same_city else "Yes",
    })

# STEP 3: Teacher allocation
# Rule: each center with >=1 girl student must have at least 1 female teacher.
# Assign teachers preferentially to their home-city center(s); balance load; ensure female coverage.

center_girls_count = defaultdict(int)
center_total_students = defaultdict(int)
for r in results:
    center_total_students[r["assigned_center"]] += 1
    if r["gender"] == "F":
        center_girls_count[r["assigned_center"]] += 1

# how many invigilators needed per center (1 per 20 students, min 1)
center_teacher_need = {}
for c in centers:
    n_students = center_total_students.get(c["center_id"], 0)
    need = max(1, -(-n_students // 20))  # ceil division
    center_teacher_need[c["center_id"]] = need

# group teachers by home city and gender
teachers_by_city = defaultdict(list)
for t in teachers:
    teachers_by_city[t["home_city"]].append(t)

assigned_teacher_ids = set()
teacher_assignment = defaultdict(list)  # center_id -> list of teacher_id

def assign_teacher_to_center(center_id, require_female=False):
    city = center_by_id[center_id]["city"]
    pool = [t for t in teachers_by_city[city] if t["teacher_id"] not in assigned_teacher_ids]
    if require_female:
        pool_f = [t for t in pool if t["gender"] == "F"]
        if pool_f:
            t = pool_f[0]
            assigned_teacher_ids.add(t["teacher_id"])
            teacher_assignment[center_id].append(t["teacher_id"])
            return True
        return False
    else:
        if pool:
            t = pool[0]
            assigned_teacher_ids.add(t["teacher_id"])
            teacher_assignment[center_id].append(t["teacher_id"])
            return True
        return False

# First pass: ensure female-teacher coverage at centers with girl students
female_coverage_gap = []
for c in centers:
    cid = c["center_id"]
    if center_girls_count.get(cid, 0) > 0:
        ok = assign_teacher_to_center(cid, require_female=True)
        if not ok:
            female_coverage_gap.append(cid)

# Second pass: fill remaining teacher needs per center with any available same-city teacher
for c in centers:
    cid = c["center_id"]
    while len(teacher_assignment[cid]) < center_teacher_need[cid]:
        ok = assign_teacher_to_center(cid, require_female=False)
        if not ok:
            break

# Any centers still short-staffed, note it
teacher_shortfall = []
for c in centers:
    cid = c["center_id"]
    have = len(teacher_assignment[cid])
    need = center_teacher_need[cid]
    if have < need:
        teacher_shortfall.append((cid, have, need))

# ---------- Save outputs ----------
with open("student_allocation.csv","w",newline="") as f:
    fieldnames = ["student_id","name","gender","home_city","pref1_city","pref2_city",
                  "assigned_center","assigned_city","assigned_via","traveled_outside_home_city"]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(results)

teacher_rows = []
for cid, tlist in teacher_assignment.items():
    for tid in tlist:
        t = next(t for t in teachers if t["teacher_id"]==tid)
        teacher_rows.append({
            "teacher_id": tid,
            "name": t["name"],
            "gender": t["gender"],
            "home_city": t["home_city"],
            "assigned_center": cid,
            "assigned_city": center_by_id[cid]["city"],
            "same_city_as_home": "Yes" if t["home_city"]==center_by_id[cid]["city"] else "No",
        })
with open("teacher_allocation.csv","w",newline="") as f:
    fieldnames = ["teacher_id","name","gender","home_city","assigned_center","assigned_city","same_city_as_home"]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(teacher_rows)

# ---------- Metrics ----------
total_students = len(results)
pref1_count = sum(1 for r in results if r["assigned_via"]=="pref1")
pref2_count = sum(1 for r in results if r["assigned_via"]=="pref2")
overflow_count = sum(1 for r in results if r["assigned_via"]=="overflow")
girls_same_city = sum(1 for r in results if r["gender"]=="F" and r["traveled_outside_home_city"]=="No")
girls_total = sum(1 for r in results if r["gender"]=="F")
boys_same_city = sum(1 for r in results if r["gender"]=="M" and r["traveled_outside_home_city"]=="No")
boys_total = sum(1 for r in results if r["gender"]=="M")

print("=== ALLOCATION SUMMARY ===")
print(f"Total students allocated: {total_students} / {len(students)}")
print(f"  via 1st preference: {pref1_count}")
print(f"  via 2nd preference: {pref2_count}")
print(f"  via overflow: {overflow_count}")
print(f"Still unallocated: {len(still_unallocated)}")
print(f"Girls kept in home city: {girls_same_city}/{girls_total} ({girls_same_city/girls_total*100:.1f}%)")
print(f"Boys kept in home city: {boys_same_city}/{boys_total} ({boys_same_city/boys_total*100:.1f}%)")
print()
print("=== TEACHER ALLOCATION ===")
print(f"Total teachers assigned: {len(teacher_rows)} / {len(teachers)}")
print(f"Centers requiring female coverage: {sum(1 for c in centers if center_girls_count.get(c['center_id'],0)>0)}")
print(f"Female-coverage gaps: {female_coverage_gap if female_coverage_gap else 'None'}")
print(f"Teacher shortfalls (center, have, need): {teacher_shortfall if teacher_shortfall else 'None'}")

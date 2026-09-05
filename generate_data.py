import random
random.seed(11)

cities = ["Delhi","Jaipur","Kota","Ajmer","Udaipur","Jodhpur","Bikaner","Alwar"]

centers = []
cid = 1
for city in cities:
    n_centers = 1  # one center per city, tighter capacity to force overflow
    for _ in range(n_centers):
        cap = random.choice([22,25,28,30])
        centers.append({"center_id": f"C{cid:03d}", "city": city, "capacity": cap})
        cid += 1

students = []
first_names_m = ["Aman","Raj","Vikas","Rohit","Karan","Suresh","Manish","Deepak","Naveen","Ashok"]
first_names_f = ["Priya","Anjali","Neha","Pooja","Kavita","Sneha","Ritu","Shweta","Divya","Meena"]

sid = 1
for city in cities:
    n_students = random.randint(20,27)  # more students than capacity in some cities -> forces pref2
    for _ in range(n_students):
        gender = random.choice(["M","F"])
        name = random.choice(first_names_m if gender=="M" else first_names_f) + f" {sid}"
        pref1 = city
        other_cities = [c for c in cities if c != city]
        pref2 = random.choice(other_cities)
        students.append({
            "student_id": f"S{sid:04d}",
            "name": name,
            "gender": gender,
            "home_city": city,
            "pref1_city": pref1,
            "pref2_city": pref2,
        })
        sid += 1

random.shuffle(students)

teacher_names_m = ["Mr. Sharma","Mr. Verma","Mr. Gupta","Mr. Yadav","Mr. Mishra","Mr. Singh","Mr. Chauhan","Mr. Joshi"]
teacher_names_f = ["Mrs. Kapoor","Ms. Rathore","Mrs. Agarwal","Ms. Bansal","Mrs. Saxena","Ms. Malhotra","Mrs. Nair","Ms. Iyer"]

teachers = []
tid = 1
for city in cities:
    n_teachers = random.randint(2,3)
    for _ in range(n_teachers):
        gender = random.choice(["M","F"])
        base_name = random.choice(teacher_names_m if gender=="M" else teacher_names_f)
        teachers.append({
            "teacher_id": f"T{tid:03d}",
            "name": f"{base_name} {tid}",
            "gender": gender,
            "home_city": city,
        })
        tid += 1

import csv
with open("centers.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=["center_id","city","capacity"])
    w.writeheader(); w.writerows(centers)

with open("students.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=["student_id","name","gender","home_city","pref1_city","pref2_city"])
    w.writeheader(); w.writerows(students)

with open("teachers.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=["teacher_id","name","gender","home_city"])
    w.writeheader(); w.writerows(teachers)

print("Centers:", len(centers), "| total capacity:", sum(c['capacity'] for c in centers))
print("Students:", len(students), " (F:", sum(1 for s in students if s['gender']=='F'), ", M:", sum(1 for s in students if s['gender']=='M'), ")")
print("Teachers:", len(teachers))

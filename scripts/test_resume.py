from models.resume import Resume
from models.skill import Skill

print("===== Resume Model Test =====")

resume = Resume(
    name="navneet prakash yadav",
    email="navneet@example.com",
    skills=[
        Skill(name="python"),
        Skill(name="sql"),
        Skill(name="pytorch")
    ],
    raw_text="Experienced Python developer with ML projects."
)

print(resume)

print("\nTesting invalid email...")

try:
    Resume(
        name="Navneet",
        email="invalid-email",
        raw_text="Resume",
    )
except Exception as e:
    print("✅ Validation worked!")
    print(e)

print("\nTesting empty name...")

try:
    Resume(
        name="   ",
        email="navneet@example.com",
        raw_text="Resume",
    )
except Exception as e:
    print("✅ Validation worked!")
    print(e)

print("\nTesting empty resume text...")

try:
    Resume(
        name="Navneet",
        email="navneet@example.com",
        raw_text="   ",
    )
except Exception as e:
    print("✅ Validation worked!")
    print(e)
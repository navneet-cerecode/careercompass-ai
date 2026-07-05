from models.skill import Skill

print("===== Skill Model Tests =====")

skill1 = Skill(name="Python")
print(skill1)

skill2 = Skill(name=" python ")
print(skill2)

skill3 = Skill(name="PYTORCH", category="Framework")
print(skill3)

try:
    Skill(name="   ")
except Exception as e:
    print("\nValidation Test Passed!")
    print(e)
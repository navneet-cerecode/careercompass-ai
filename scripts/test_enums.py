"""
Tests the enum models.
"""

from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)


print("Experience Levels:")
for level in ExperienceLevel:
    print(level)

print("\nEmployment Types:")
for employment in EmploymentType:
    print(employment)

print("\nJob Sources:")
for source in JobSource:
    print(source)
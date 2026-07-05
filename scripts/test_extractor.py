from services.resume.parser_service import ResumeParserService

from services.resume.extractor import ResumeExtractor

parser = ResumeParserService()

extractor = ResumeExtractor()

path = input("Resume Path: ")

text = parser.parse(path)

resume = extractor.extract(text)

print()

print("=" * 50)

print("NAME")

print(resume.name)

print()

print("EMAIL")

print(resume.email)

print()

print("PHONE")

print(resume.phone)

print()

print("LINKEDIN")

print(resume.linkedin)

print()

print("GITHUB")

print(resume.github)

print()

print("SKILLS")

for skill in resume.skills:

    print("-", skill.name)
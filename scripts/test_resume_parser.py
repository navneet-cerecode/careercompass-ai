from services.resume.parser_service import ResumeParserService

parser = ResumeParserService()

resume_path = input("Enter resume path: ")

text = parser.parse(resume_path)

print("\n========== RESUME ==========\n")

print(text[:3000])

print("\n============================")
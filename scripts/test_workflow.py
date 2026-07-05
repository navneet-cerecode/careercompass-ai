from graph.workflow import graph

initial_state = {
    "role": "Data Scientist",
    "location": "India",
    "resume": None,
    "jobs": [],
    "match_results": [],
}

result = graph.invoke(initial_state)

print("\n========== FINAL STATE ==========\n")

print(result)

print("\n========== JOBS ==========\n")

print(result["jobs"])

print("\n========== MATCH RESULTS ==========\n")

print(result["match_results"])
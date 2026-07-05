from graph.nodes import (
    candidate_evaluation_node,
    job_discovery_node,
)

state = {
    "role": "Data Scientist",
    "location": "India",
    "resume": None,
    "jobs": [],
    "match_results": [],
}

state = job_discovery_node(state)

print("\nJobs Found\n")
print(state["jobs"])

state = candidate_evaluation_node(state)

print("\nMatch Results\n")
print(state["match_results"])
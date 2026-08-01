import { describe, expect, it } from "vitest";

import {
  buildJobSearchRequest,
  buildRecommendationRequest,
} from "@/lib/api/job-contract";

describe("job workflow contract helpers", () => {
  it("normalizes role preferences into the generated search contract", () => {
    expect(
      buildJobSearchRequest({
        role: "  AI Engineer ",
        location: " Bengaluru ",
        country: "in",
        remoteOnly: true,
        employmentTypes: ["Full Time", "Contract"],
        datePosted: "week",
      }),
    ).toEqual({
      role: "AI Engineer",
      location: "Bengaluru",
      country: "IN",
      page: 1,
      page_size: 20,
      remote_only: true,
      employment_types: ["Full Time", "Contract"],
      date_posted: "week",
    });
  });

  it("preserves reviewed resume evidence when building a ranking request", () => {
    const request = buildRecommendationRequest(
      {
        resume: {
          id: "d8a45758-b7b2-4896-bf85-48051b9c077e",
          name: "Ada Lovelace",
          email: "ada@example.com",
          education: [],
          experience: ["Built an analytical engine program"],
          projects: [],
          skills: [{ name: "Python", category: "technical" }],
          certifications: [],
          achievements: [],
        },
        raw_text: "Ada Lovelace\nPython engineer",
      },
      [
        {
          id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
          title: "AI Engineer",
          company: "Analytical Engines",
          location: "Remote",
          description: "Build reliable systems.",
          required_skills: [],
          experience_level: "Entry",
          employment_type: "Full Time",
          source: "JSearch",
          url: "https://example.com/job",
        },
      ],
    );

    expect(request.job_ids).toEqual([
      "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
    ]);
    expect(request.resume.raw_text).toBe("Ada Lovelace\nPython engineer");
    expect(request.resume.experience).toEqual([
      "Built an analytical engine program",
    ]);
  });
});

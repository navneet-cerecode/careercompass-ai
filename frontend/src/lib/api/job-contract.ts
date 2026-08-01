import type { components } from "@/lib/api/schema";
import type { ParsedResumeResponse } from "@/lib/api/resume-contract";

export type JobSearchRequest = components["schemas"]["JobSearchRequest"];
export type JobSearchResponse = components["schemas"]["JobSearchResponse"];
export type JobResponse = components["schemas"]["JobResponse"];
export type RecommendationRequest =
  components["schemas"]["RecommendationRequest"];
export type RecommendationBatchResponse =
  components["schemas"]["RecommendationBatchResponse"];
export type JobRecommendation =
  components["schemas"]["JobRecommendationResponse"];
export type EmploymentType = components["schemas"]["EmploymentType"];
export type DatePosted = components["schemas"]["DatePosted"];

export type RolePreferences = {
  role: string;
  location: string;
  country?: string;
  remoteOnly: boolean;
  employmentTypes: EmploymentType[];
  datePosted: DatePosted;
};

export function buildJobSearchRequest(
  preferences: RolePreferences,
): JobSearchRequest {
  return {
    role: preferences.role.trim(),
    location: preferences.location.trim(),
    country: preferences.country?.trim().toUpperCase() || null,
    page: 1,
    page_size: 20,
    remote_only: preferences.remoteOnly || null,
    employment_types: preferences.employmentTypes,
    date_posted: preferences.datePosted,
  };
}

export function buildRecommendationRequest(
  profile: ParsedResumeResponse,
  jobs: JobResponse[],
): RecommendationRequest {
  return {
    resume: {
      ...profile.resume,
      raw_text: profile.raw_text,
    },
    job_ids: jobs.map((job) => job.id),
  };
}

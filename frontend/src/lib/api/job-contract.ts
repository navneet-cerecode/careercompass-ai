import type { components } from "@/lib/api/schema";
import type { ParsedResumeResponse } from "@/lib/api/resume-contract";

export type JobSearchRequest = components["schemas"]["JobSearchRequest"];
export type JobSearchResponse = components["schemas"]["JobSearchResponse"];
export type JobSearchTaskCreatedResponse =
  components["schemas"]["JobSearchTaskCreatedResponse"];
export type JobSearchTaskResponse =
  components["schemas"]["JobSearchTaskResponse"];
export type JobResponse = components["schemas"]["JobResponse"];
export type RecommendationRequest =
  components["schemas"]["RecommendationRequest"];
export type RecommendationBatchResponse =
  components["schemas"]["RecommendationBatchResponse"];
export type JobRecommendation =
  components["schemas"]["JobRecommendationResponse"];
export type SaveJobRequest = components["schemas"]["SaveJobRequest"];
export type SavedJobResponse = components["schemas"]["SavedJobResponse"];
export type SavedJobListResponse =
  components["schemas"]["SavedJobListResponse"];
export type ApplicationStatus = components["schemas"]["ApplicationStatus"];
export type ApplicationResponse = components["schemas"]["ApplicationResponse"];
export type ApplicationDetailResponse =
  components["schemas"]["ApplicationDetailResponse"];
export type ApplicationEventResponse =
  components["schemas"]["ApplicationEventResponse"];
export type ApplicationListResponse =
  components["schemas"]["ApplicationListResponse"];
export type CreateApplicationRequest =
  components["schemas"]["CreateApplicationRequest"];
export type TransitionApplicationRequest =
  components["schemas"]["TransitionApplicationRequest"];
export type UpdateApplicationPlanRequest =
  components["schemas"]["UpdateApplicationPlanRequest"];
export type ApplicationPacketResponse =
  components["schemas"]["ApplicationPacketResponse"];
export type UpdateApplicationPacketRequest =
  components["schemas"]["UpdateApplicationPacketRequest"];
export type ConfirmExternalSubmissionRequest =
  components["schemas"]["ConfirmExternalSubmissionRequest"];
export type ApplicationReminderStatus =
  components["schemas"]["ApplicationReminderStatus"];
export type ApplicationReminderResponse =
  components["schemas"]["ApplicationReminderResponse"];
export type ApplicationReminderListResponse =
  components["schemas"]["ApplicationReminderListResponse"];
export type UpdateApplicationReminderRequest =
  components["schemas"]["UpdateApplicationReminderRequest"];
export type BillingSummaryResponse =
  components["schemas"]["BillingSummaryResponse"];
export type EntitlementsResponse =
  components["schemas"]["EntitlementsResponse"];
export type CreateTailoringPlanRequest =
  components["schemas"]["CreateTailoringPlanRequest"];
export type TailoringPlanResponse =
  components["schemas"]["TailoringPlanResponse"];
export type CreateTailoredResumeRequest =
  components["schemas"]["CreateTailoredResumeRequest"];
export type TailoredResumeResponse =
  components["schemas"]["TailoredResumeResponse"];
export type TailoredResumeSelectionsRequest =
  components["schemas"]["TailoredResumeSelectionsRequest"];
export type TailoredResumeVersionListResponse =
  components["schemas"]["TailoredResumeVersionListResponse"];
export type CreateCoverLetterRequest =
  components["schemas"]["CreateCoverLetterRequest"];
export type CoverLetterContentRequest =
  components["schemas"]["CoverLetterContentRequest"];
export type CoverLetterResponse =
  components["schemas"]["CoverLetterResponse"];
export type CoverLetterVersionListResponse =
  components["schemas"]["CoverLetterVersionListResponse"];
export type SubscriptionPlan = components["schemas"]["SubscriptionPlan"];
export type SubscriptionStatus = components["schemas"]["SubscriptionStatus"];
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

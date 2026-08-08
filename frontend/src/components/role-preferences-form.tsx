"use client";

import { type FormEvent, useState } from "react";

import type {
  DatePosted,
  EmploymentType,
  RolePreferences,
} from "@/lib/api/job-contract";

type RolePreferencesFormProps = {
  initialPreferences: RolePreferences;
  onBack: () => void;
  onSubmit: (preferences: RolePreferences) => void;
};

const EMPLOYMENT_OPTIONS: {
  value: EmploymentType;
  label: string;
  detail: string;
}[] = [
  { value: "Full Time", label: "Full time", detail: "Permanent roles" },
  { value: "Internship", label: "Internship", detail: "Structured learning" },
  { value: "Contract", label: "Contract", detail: "Project-based work" },
  { value: "Part Time", label: "Part time", detail: "Reduced schedule" },
];

const DATE_OPTIONS: { value: DatePosted; label: string }[] = [
  { value: "week", label: "Past week" },
  { value: "month", label: "Past month" },
  { value: "all", label: "Any time" },
];

export function RolePreferencesForm({
  initialPreferences,
  onBack,
  onSubmit,
}: RolePreferencesFormProps) {
  const [preferences, setPreferences] =
    useState<RolePreferences>(initialPreferences);
  const [error, setError] = useState<string | null>(null);

  const toggleEmploymentType = (value: EmploymentType) => {
    setPreferences((current) => ({
      ...current,
      employmentTypes: current.employmentTypes.includes(value)
        ? current.employmentTypes.filter((item) => item !== value)
        : [...current.employmentTypes, value],
    }));
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!preferences.role.trim()) {
      setError("Add the role or career lane you want to explore.");
      return;
    }

    if (!preferences.location.trim()) {
      setError("Add a city, region, country, or Remote.");
      return;
    }

    setError(null);
    onSubmit(preferences);
  };

  return (
    <form
      className="preferences-form"
      onSubmit={handleSubmit}
      aria-labelledby="preferences-title"
    >
      <div className="preferences-heading">
        <span className="review-kicker">
          <span aria-hidden="true">02</span>
          Search direction
        </span>
        <h2 id="preferences-title">What deserves your attention?</h2>
        <p>
          Give Solara Hire a focused lane. You can refine it after seeing the
          first ranked set.
        </p>
      </div>

      <div className="field-grid">
        <label className="field field-wide">
          <span>Role or career lane</span>
          <input
            name="role"
            type="text"
            value={preferences.role}
            placeholder="e.g. Registered Nurse or Sales Manager"
            autoComplete="organization-title"
            onChange={(event) =>
              setPreferences((current) => ({
                ...current,
                role: event.target.value,
              }))
            }
          />
          <small>Use the title employers are likely to publish.</small>
        </label>

        <label className="field">
          <span>Location</span>
          <input
            name="location"
            type="text"
            value={preferences.location}
            placeholder="India, Bengaluru, or Remote"
            autoComplete="address-level2"
            onChange={(event) =>
              setPreferences((current) => ({
                ...current,
                location: event.target.value,
              }))
            }
          />
        </label>

        <label className="field country-field">
          <span>Country code</span>
          <input
            name="country"
            type="text"
            value={preferences.country ?? ""}
            placeholder="IN"
            maxLength={2}
            autoComplete="country"
            onChange={(event) =>
              setPreferences((current) => ({
                ...current,
                country: event.target.value.replace(/[^a-z]/gi, "").slice(0, 2),
              }))
            }
          />
        </label>
      </div>

      <fieldset className="preference-group">
        <legend>Work arrangement</legend>
        <label className="remote-toggle">
          <span>
            <strong>Remote roles only</strong>
            <small>Exclude on-site and hybrid results</small>
          </span>
          <input
            type="checkbox"
            checked={preferences.remoteOnly}
            onChange={(event) =>
              setPreferences((current) => ({
                ...current,
                remoteOnly: event.target.checked,
              }))
            }
          />
          <span className="toggle-track" aria-hidden="true">
            <span />
          </span>
        </label>
      </fieldset>

      <fieldset className="preference-group">
        <legend>Employment type</legend>
        <div className="employment-options">
          {EMPLOYMENT_OPTIONS.map((option) => (
            <label key={option.value} className="employment-option">
              <input
                type="checkbox"
                checked={preferences.employmentTypes.includes(option.value)}
                onChange={() => toggleEmploymentType(option.value)}
              />
              <span className="option-check" aria-hidden="true">
                ✓
              </span>
              <span>
                <strong>{option.label}</strong>
                <small>{option.detail}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="preference-group">
        <legend>Freshness</legend>
        <div className="date-options">
          {DATE_OPTIONS.map((option) => (
            <label key={option.value}>
              <input
                type="radio"
                name="date-posted"
                value={option.value}
                checked={preferences.datePosted === option.value}
                onChange={() =>
                  setPreferences((current) => ({
                    ...current,
                    datePosted: option.value,
                  }))
                }
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="preference-feedback" role="status" aria-live="polite">
        {error && (
          <>
            <span aria-hidden="true">!</span>
            {error}
          </>
        )}
      </div>

      <div className="preference-actions">
        <button className="button button-quiet" type="button" onClick={onBack}>
          ← Review profile
        </button>
        <button className="button match-button" type="submit">
          Find and rank jobs
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}

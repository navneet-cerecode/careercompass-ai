"use client";

import { type FormEvent, useState } from "react";

import type { ParsedResumeResponse } from "@/lib/api/resume-contract";

type ResumeProfile = ParsedResumeResponse["resume"];

type CandidateProfileEditorProps = {
  profile: ResumeProfile;
  onCancel: () => void;
  onSave: (profile: ResumeProfile) => void;
};

type ProfileDraft = {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
  skills: string;
  experience: string;
  education: string;
  projects: string;
  certifications: string;
  achievements: string;
};

const listFields = [
  "experience",
  "education",
  "projects",
  "certifications",
  "achievements",
] as const;

type ListField = (typeof listFields)[number];

const listFieldLabels: Record<ListField, string> = {
  experience: "Experience",
  education: "Education",
  projects: "Projects",
  certifications: "Certifications",
  achievements: "Achievements",
};

const listItemLabels: Record<ListField, string> = {
  experience: "experience item",
  education: "education item",
  projects: "project",
  certifications: "certification",
  achievements: "achievement",
};

function toDraft(profile: ResumeProfile): ProfileDraft {
  return {
    name: profile.name,
    email: profile.email ?? "",
    phone: profile.phone ?? "",
    linkedin: profile.linkedin ?? "",
    github: profile.github ?? "",
    skills: profile.skills.map((skill) => skill.name).join(", "),
    experience: profile.experience.join("\n"),
    education: profile.education.join("\n"),
    projects: profile.projects.join("\n"),
    certifications: profile.certifications.join("\n"),
    achievements: profile.achievements.join("\n"),
  };
}

function cleanOptional(value: string): string | null {
  const cleaned = value.trim();
  return cleaned.length > 0 ? cleaned : null;
}

function cleanLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildProfile(
  original: ResumeProfile,
  draft: ProfileDraft,
): ResumeProfile {
  const originalSkills = new Map(
    original.skills.map((skill) => [skill.name.trim().toLowerCase(), skill]),
  );
  const seenSkills = new Set<string>();
  const skills = draft.skills
    .split(/,|\n/)
    .map((name) => name.trim())
    .filter((name) => {
      const key = name.toLowerCase();
      if (!name || seenSkills.has(key)) {
        return false;
      }
      seenSkills.add(key);
      return true;
    })
    .map((name) => {
      const existing = originalSkills.get(name.toLowerCase());
      return {
        name,
        category: existing?.category ?? null,
      };
    });

  return {
    ...original,
    name: draft.name.trim(),
    email: cleanOptional(draft.email),
    phone: cleanOptional(draft.phone),
    linkedin: cleanOptional(draft.linkedin),
    github: cleanOptional(draft.github),
    skills,
    experience: cleanLines(draft.experience),
    education: cleanLines(draft.education),
    projects: cleanLines(draft.projects),
    certifications: cleanLines(draft.certifications),
    achievements: cleanLines(draft.achievements),
  };
}

export function CandidateProfileEditor({
  profile,
  onCancel,
  onSave,
}: CandidateProfileEditorProps) {
  const [draft, setDraft] = useState(() => toDraft(profile));
  const [error, setError] = useState<string | null>(null);

  const updateField = (field: keyof ProfileDraft, value: string) => {
    setDraft((current) => ({ ...current, [field]: value }));
    setError(null);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!draft.name.trim()) {
      setError("Add your name before saving the reviewed profile.");
      return;
    }

    if (
      draft.email.trim() &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(draft.email.trim())
    ) {
      setError("Enter a complete email address or leave the field empty.");
      return;
    }

    onSave(buildProfile(profile, draft));
  };

  return (
    <form
      className="profile-editor"
      onSubmit={handleSubmit}
      aria-labelledby="profile-editor-title"
      noValidate
    >
      <div className="profile-editor-heading">
        <div>
          <span className="micro-label">Candidate corrections</span>
          <h3 id="profile-editor-title">Make the profile true to your resume.</h3>
          <p>
            Correct parsing mistakes only. Your uploaded source text remains
            unchanged and these edits stay in this browser session.
          </p>
        </div>
        <span className="profile-state is-editing">Editing</span>
      </div>

      <div className="identity-fields">
        <label className="profile-field profile-field-wide">
          <span>Name *</span>
          <input
            name="name"
            value={draft.name}
            onChange={(event) => updateField("name", event.target.value)}
            autoComplete="name"
            required
          />
        </label>
        <label className="profile-field">
          <span>Email</span>
          <input
            name="email"
            type="email"
            value={draft.email}
            onChange={(event) => updateField("email", event.target.value)}
            autoComplete="email"
          />
        </label>
        <label className="profile-field">
          <span>Phone</span>
          <input
            name="phone"
            value={draft.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            autoComplete="tel"
          />
        </label>
        <label className="profile-field">
          <span>LinkedIn</span>
          <input
            name="linkedin"
            value={draft.linkedin}
            onChange={(event) => updateField("linkedin", event.target.value)}
            autoComplete="url"
          />
        </label>
        <label className="profile-field">
          <span>GitHub</span>
          <input
            name="github"
            value={draft.github}
            onChange={(event) => updateField("github", event.target.value)}
            autoComplete="url"
          />
        </label>
      </div>

      <label className="profile-field profile-field-block">
        <span>Skills</span>
        <textarea
          name="skills"
          value={draft.skills}
          onChange={(event) => updateField("skills", event.target.value)}
          rows={3}
          placeholder="Python, SQL, data analysis"
        />
        <small>Separate skills with commas.</small>
      </label>

      <div className="profile-list-fields">
        {listFields.map((field) => (
          <label className="profile-field" key={field}>
            <span>{listFieldLabels[field]}</span>
            <textarea
              name={field}
              value={draft[field]}
              onChange={(event) => updateField(field, event.target.value)}
              rows={4}
              placeholder={`One ${listItemLabels[field]} per line`}
            />
          </label>
        ))}
      </div>

      {error && (
        <div className="profile-editor-error" role="alert">
          <span aria-hidden="true">!</span>
          {error}
        </div>
      )}

      <div className="profile-editor-actions">
        <button className="button button-quiet" type="button" onClick={onCancel}>
          Cancel
        </button>
        <button className="button profile-save" type="submit">
          Save reviewed profile
          <span aria-hidden="true">✓</span>
        </button>
      </div>
    </form>
  );
}

"use client";

import {
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
  useRef,
  useState,
} from "react";

import {
  ACCEPTED_RESUME_EXTENSIONS,
  getApiErrorMessage,
  type ParsedResumeResponse,
  validateResumeFile,
} from "@/lib/api/resume-contract";
import { CandidateProfileEditor } from "@/components/candidate-profile-editor";

type ResumeOnboardingProps = {
  initialResult?: ParsedResumeResponse;
  onContinue?: (result: ParsedResumeResponse) => void;
};

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "error"; message: string }
  | { status: "success"; result: ParsedResumeResponse };

const ACCEPT_ATTRIBUTE = ACCEPTED_RESUME_EXTENSIONS.join(",");

function ProfileList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="profile-section">
      <span className="micro-label">{title}</span>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function ResumeOnboarding({
  initialResult,
  onContinue,
}: ResumeOnboardingProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileCorrected, setProfileCorrected] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>(
    initialResult
      ? { status: "success", result: initialResult }
      : { status: "idle" },
  );

  const chooseFile = (nextFile: File | null) => {
    if (!nextFile) {
      return;
    }

    const validationMessage = validateResumeFile(nextFile);
    setFile(validationMessage ? null : nextFile);
    setUploadState(
      validationMessage
        ? { status: "error", message: validationMessage }
        : { status: "idle" },
    );
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    chooseFile(event.target.files?.[0] ?? null);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    chooseFile(event.dataTransfer.files[0] ?? null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!file) {
      setUploadState({
        status: "error",
        message: "Choose a resume before continuing.",
      });
      return;
    }

    setUploadState({ status: "uploading" });
    const formData = new FormData();
    formData.set("file", file, file.name);

    try {
      const response = await fetch("/api/resumes/parse", {
        method: "POST",
        body: formData,
      });
      const payload: unknown = await response.json();

      if (!response.ok) {
        setUploadState({
          status: "error",
          message:
            getApiErrorMessage(payload) ??
            "We could not read this resume. Check the file and try again.",
        });
        return;
      }

      setUploadState({
        status: "success",
        result: payload as ParsedResumeResponse,
      });
    } catch {
      setUploadState({
        status: "error",
        message:
          "CareerCompass could not reach the resume service. Try again shortly.",
      });
    }
  };

  const resetUpload = () => {
    setFile(null);
    setEditingProfile(false);
    setProfileCorrected(false);
    setUploadState({ status: "idle" });
    if (inputRef.current) {
      inputRef.current.value = "";
      inputRef.current.focus();
    }
  };

  if (uploadState.status === "success") {
    const { resume, raw_text: rawText } = uploadState.result;
    const contactDetails = [resume.email, resume.phone].filter(
      (value): value is string => Boolean(value),
    );
    const links = [resume.linkedin, resume.github].filter(
      (value): value is string => Boolean(value),
    );

    return (
      <section
        className="profile-review"
        aria-labelledby="profile-review-title"
      >
        <div className="review-heading">
          <div>
            <span className="review-kicker">
              <span aria-hidden="true">✓</span>
              Resume parsed
            </span>
            <h2 id="profile-review-title">Review what we found.</h2>
            <p>
              This profile comes directly from your resume. Nothing has been
              added or embellished.
            </p>
          </div>
          <button className="text-button" type="button" onClick={resetUpload}>
            Choose another file
          </button>
        </div>

        <div className="profile-sheet">
          {editingProfile ? (
            <CandidateProfileEditor
              profile={resume}
              onCancel={() => setEditingProfile(false)}
              onSave={(reviewedProfile) => {
                setUploadState({
                  status: "success",
                  result: {
                    ...uploadState.result,
                    resume: reviewedProfile,
                  },
                });
                setProfileCorrected(true);
                setEditingProfile(false);
              }}
            />
          ) : (
            <>
              <div className="profile-identity">
                <div>
                  <span className="micro-label">Candidate profile</span>
                  <h3>{resume.name}</h3>
                </div>
                <div className="profile-identity-actions">
                  <span className="profile-state">
                    {profileCorrected
                      ? "Corrected in session"
                      : "Ready for review"}
                  </span>
                  <button
                    className="text-button profile-edit-button"
                    type="button"
                    onClick={() => setEditingProfile(true)}
                  >
                    Correct profile
                  </button>
                </div>
              </div>

              {(contactDetails.length > 0 || links.length > 0) && (
                <div className="profile-contact" aria-label="Contact details">
                  {[...contactDetails, ...links].map((detail) => (
                    <span key={detail}>{detail}</span>
                  ))}
                </div>
              )}

              <div className="profile-grid">
                <section className="profile-section skill-section">
                  <span className="micro-label">Skills detected</span>
                  {resume.skills.length > 0 ? (
                    <div className="skill-cloud">
                      {resume.skills.map((skill) => (
                        <span key={`${skill.name}-${skill.category}`}>
                          {skill.name}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-profile-copy">
                      No explicit skills were detected. Review the source text
                      before matching.
                    </p>
                  )}
                </section>

                <ProfileList title="Experience" items={resume.experience} />
                <ProfileList title="Education" items={resume.education} />
                <ProfileList title="Projects" items={resume.projects} />
                <ProfileList
                  title="Certifications"
                  items={resume.certifications}
                />
                <ProfileList title="Achievements" items={resume.achievements} />
              </div>

              <details className="source-text">
                <summary>Inspect original source text</summary>
                <p>
                  This is the exact uploaded text. Corrections update the
                  structured profile used for this session, never the source.
                </p>
                <pre>{rawText}</pre>
              </details>
            </>
          )}
        </div>

        <div className={`review-next ${editingProfile ? "is-disabled" : ""}`}>
          <span className="review-next-number">02</span>
          <div>
            <strong>Next: define the roles you want</strong>
            <span>
              We will use this reviewed evidence to search and rank jobs.
            </span>
          </div>
          {onContinue && (
            <button
              className="button review-continue"
              type="button"
              disabled={editingProfile}
              onClick={() => onContinue(uploadState.result)}
            >
              Set preferences
              <span aria-hidden="true">→</span>
            </button>
          )}
        </div>
      </section>
    );
  }

  return (
    <form
      className="resume-form"
      onSubmit={handleSubmit}
      aria-label="Resume upload"
      aria-busy={uploadState.status === "uploading"}
      noValidate
    >
      <div
        className={`upload-zone ${dragActive ? "is-dragging" : ""} ${
          file ? "has-file" : ""
        }`}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node)) {
            setDragActive(false);
          }
        }}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          className="file-input"
          id="resume-file"
          name="file"
          type="file"
          accept={ACCEPT_ATTRIBUTE}
          onChange={handleFileChange}
          aria-describedby="resume-file-help resume-file-status"
        />

        <div className="upload-icon" aria-hidden="true">
          <span>↑</span>
        </div>

        {file ? (
          <>
            <span className="micro-label">Ready to parse</span>
            <h2>{file.name}</h2>
            <p>{(file.size / 1024).toFixed(1)} KB · Stored only for review</p>
            <label className="text-button" htmlFor="resume-file">
              Replace file
            </label>
          </>
        ) : (
          <>
            <span className="micro-label">Start with the truth</span>
            <h2>Drop your resume here.</h2>
            <p id="resume-file-help">
              PDF, DOCX, or TXT · 5 MB maximum · Never used to invent
              experience
            </p>
            <label className="button button-secondary" htmlFor="resume-file">
              Browse files
            </label>
          </>
        )}
      </div>

      <div
        id="resume-file-status"
        className={`upload-feedback ${
          uploadState.status === "error" ? "is-error" : ""
        }`}
        role="status"
        aria-live="polite"
      >
        {uploadState.status === "error" ? (
          <>
            <span aria-hidden="true">!</span>
            {uploadState.message}
          </>
        ) : (
          <>
            <span aria-hidden="true">i</span>
            Your resume is parsed for review before any matching begins.
          </>
        )}
      </div>

      <button
        className="button button-primary upload-submit"
        type="submit"
        disabled={!file || uploadState.status === "uploading"}
      >
        {uploadState.status === "uploading"
          ? "Reading your resume…"
          : "Build my profile"}
        <span aria-hidden="true">→</span>
      </button>
    </form>
  );
}

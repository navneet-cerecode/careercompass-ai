import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResumeOnboarding } from "@/components/resume-onboarding";

const parsedResume = {
  resume: {
    id: "a3877e65-a19c-496d-a73f-a64d29766468",
    name: "Ada Lovelace",
    email: "ada@example.com",
    phone: null,
    linkedin: null,
    github: "github.com/ada",
    education: ["BSc Mathematics"],
    experience: ["Built the Analytical Engine program"],
    projects: [],
    skills: [
      { name: "Python", category: "technical" },
      { name: "SQL", category: "technical" },
    ],
    certifications: [],
    achievements: [],
  },
  raw_text: "Ada Lovelace\nada@example.com\nPython and SQL",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ResumeOnboarding", () => {
  it("starts with an accessible, disabled upload flow", () => {
    render(<ResumeOnboarding />);

    expect(
      screen.getByRole("heading", { name: "Drop your resume here." }),
    ).toBeInTheDocument();
    const fileInput = screen.getByLabelText("Browse files");
    expect(fileInput).toHaveAttribute("type", "file");
    expect(fileInput).toHaveAttribute("accept", ".pdf,.docx,.txt");
    expect(fileInput).toHaveClass("file-input");
    expect(
      screen.queryByRole("button", { name: "Paste resume text" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Build my profile/ }),
    ).toBeDisabled();
  });

  it("rejects unsupported files before making a request", async () => {
    const user = userEvent.setup({ applyAccept: false });
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<ResumeOnboarding />);

    await user.upload(
      screen.getByLabelText("Browse files"),
      new File(["resume"], "resume.rtf", { type: "application/rtf" }),
    );

    expect(
      screen.getByText("Choose a PDF, DOCX, or plain-text resume."),
    ).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("uploads a resume and renders only the parsed profile", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json(parsedResume, {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<ResumeOnboarding />);

    await user.upload(
      screen.getByLabelText("Browse files"),
      new File(["Ada Lovelace"], "ada.txt", { type: "text/plain" }),
    );
    await user.click(
      screen.getByRole("button", { name: /Build my profile/ }),
    );

    expect(
      await screen.findByRole("heading", { name: "Review what we found." }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ada Lovelace" })).toBeVisible();
    expect(screen.getByText("Python")).toBeVisible();
    expect(screen.getByText("SQL")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/resumes/parse",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("continues with the user-reviewed profile while preserving source text", async () => {
    const user = userEvent.setup();
    const onContinue = vi.fn();
    render(
      <ResumeOnboarding
        initialResult={parsedResume}
        onContinue={onContinue}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Correct profile" }),
    );
    expect(
      screen.getByRole("button", { name: /Set preferences/ }),
    ).toBeDisabled();

    await user.clear(screen.getByLabelText(/^Skills/));
    await user.type(
      screen.getByLabelText(/^Skills/),
      "Python, SQL, Statistics",
    );
    await user.click(
      screen.getByRole("button", { name: /Save reviewed profile/ }),
    );
    await user.click(
      screen.getByRole("button", { name: /Set preferences/ }),
    );

    expect(onContinue).toHaveBeenCalledWith({
      raw_text: parsedResume.raw_text,
      resume: expect.objectContaining({
        skills: [
          { name: "Python", category: "technical" },
          { name: "SQL", category: "technical" },
          { name: "Statistics", category: null },
        ],
      }),
    });
  });

  it("surfaces the backend error without discarding the selected file", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(
          {
            code: "invalid_resume",
            message: "The uploaded file is not a valid PDF.",
          },
          { status: 422 },
        ),
      ),
    );
    render(<ResumeOnboarding />);

    await user.upload(
      screen.getByLabelText("Browse files"),
      new File(["not-a-pdf"], "resume.pdf", { type: "application/pdf" }),
    );
    await user.click(
      screen.getByRole("button", { name: /Build my profile/ }),
    );

    expect(
      await screen.findByText("The uploaded file is not a valid PDF."),
    ).toBeInTheDocument();
    expect(screen.getByText("resume.pdf")).toBeVisible();
  });

  it("announces that resume parsing is in progress", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => undefined)));
    render(<ResumeOnboarding />);

    await user.upload(
      screen.getByLabelText("Browse files"),
      new File(["Ada Lovelace"], "ada.txt", { type: "text/plain" }),
    );
    await user.click(
      screen.getByRole("button", { name: /Build my profile/ }),
    );

    expect(
      screen.getByRole("form", { name: "Resume upload" }),
    ).toHaveAttribute("aria-busy", "true");
  });
});

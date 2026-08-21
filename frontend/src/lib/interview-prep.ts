/**
 * Interview preparation resources (Phase 5.5).
 * Curated questions, tips, and salary benchmarks by role type.
 */

export type InterviewPrepCategory = {
  id: string;
  name: string;
  icon: string;
  questions: {
    question: string;
    tip: string;
    sampleAnswer?: string;
  }[];
};

export const INTERVIEW_PREP_CATEGORIES: InterviewPrepCategory[] = [
  {
    id: "behavioral",
    name: "Behavioral Questions",
    icon: "🧠",
    questions: [
      {
        question: "Tell me about a time you faced a challenging project.",
        tip: "Use the STAR method (Situation, Task, Action, Result). Be specific about the challenge and your measurable impact.",
        sampleAnswer: "In my previous role, we had a critical API that was failing 5% of the time under load. I identified the bottleneck in the database query layer, implemented connection pooling and query optimization, reducing failures to 0.1% and improving response time by 40%.",
      },
      {
        question: "Describe a situation where you had to work with a difficult teammate.",
        tip: "Focus on how you built the relationship and found common ground. Never speak negatively about the person.",
      },
      {
        question: "Tell me about a time you failed and what you learned.",
        tip: "Choose a genuine failure, show self-awareness, and emphasize the concrete lessons you applied afterward.",
      },
      {
        question: "How do you prioritize tasks when everything seems urgent?",
        tip: "Mention frameworks you use (Eisenhower matrix, MoSCoW) and give a real example of trade-offs you made.",
      },
    ],
  },
  {
    id: "technical",
    name: "Technical Questions",
    icon: "💻",
    questions: [
      {
        question: "Explain a complex technical concept to a non-technical stakeholder.",
        tip: "Show you can communicate clearly without jargon. Use analogies and focus on business impact.",
      },
      {
        question: "Walk me through your approach to debugging a production issue.",
        tip: "Mention monitoring, logging, replication steps, root cause analysis, and prevention.",
      },
      {
        question: "How do you ensure code quality in your team?",
        tip: "Cover code reviews, testing strategies (unit, integration, e2e), linting, and CI/CD.",
      },
      {
        question: "Describe your experience with system design.",
        tip: "Discuss trade-offs, scalability patterns, and how you evaluate requirements before jumping to solutions.",
      },
    ],
  },
  {
    id: "culture",
    name: "Culture Fit",
    icon: "🤝",
    questions: [
      {
        question: "Why do you want to work here?",
        tip: "Research the company's mission, recent achievements, and tech stack. Connect your goals to their work.",
      },
      {
        question: "What does your ideal work environment look like?",
        tip: "Align with the company's culture while being authentic. Mention collaboration, growth, and impact.",
      },
      {
        question: "Where do you see yourself in 5 years?",
        tip: "Show ambition tied to growth within the company. Mention specific skills you want to develop.",
      },
    ],
  },
  {
    id: "salary",
    name: "Salary Negotiation",
    icon: "💰",
    questions: [
      {
        question: "What are your salary expectations?",
        tip: "Research market rates on Glassdoor, Levels.fyi, and PayScale. Give a range based on the role level and location.",
      },
      {
        question: "Can you tell me about your current compensation?",
        tip: "You're not obligated to share. Redirect to the value you bring and the market rate for the role.",
      },
    ],
  },
];

export const SALARY_BENCHMARKS: Record<string, { min: number; max: number; median: number; currency: string }> = {
  "software engineer": { min: 60000, max: 180000, median: 110000, currency: "USD" },
  "frontend developer": { min: 55000, max: 160000, median: 95000, currency: "USD" },
  "backend developer": { min: 60000, max: 175000, median: 105000, currency: "USD" },
  "full stack developer": { min: 60000, max: 170000, median: 100000, currency: "USD" },
  "data scientist": { min: 70000, max: 200000, median: 120000, currency: "USD" },
  "devops engineer": { min: 65000, max: 180000, median: 115000, currency: "USD" },
  "product manager": { min: 80000, max: 200000, median: 125000, currency: "USD" },
  "ux designer": { min: 55000, max: 150000, median: 90000, currency: "USD" },
  "mobile developer": { min: 60000, max: 170000, median: 100000, currency: "USD" },
  "machine learning engineer": { min: 75000, max: 220000, median: 135000, currency: "USD" },
};

export function getSalaryBenchmark(jobTitle: string) {
  const lower = jobTitle.toLowerCase();
  for (const [key, value] of Object.entries(SALARY_BENCHMARKS)) {
    if (lower.includes(key) || key.includes(lower)) {
      return value;
    }
  }
  return null;
}

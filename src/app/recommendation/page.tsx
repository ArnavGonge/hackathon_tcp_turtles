"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ExternalLink, Link as LinkIcon } from "lucide-react";

type CourseRecommendation = {
  course_id: string;
  course_name: string;
  source_url: string;
  description: string;
};

export default function RecommendationPage() {
  const [recs, setRecs] = useState<CourseRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let active = true;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/recommendation", { cache: "no-store" });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const data = (await res.json()) as CourseRecommendation[];
        if (active) setRecs(Array.isArray(data) ? data : []);
      } catch (e: unknown) {
        console.error(e);
        // Fallback to sample when API not available
        const sample: CourseRecommendation[] = [
          {
            course_id: "C001",
            course_name: "Introduction to Programming",
            source_url: "https://www.example.com/intro-to-programming",
            description:
              "Learn the basics of programming, including variables, control structures, and functions using Python.",
          },
          {
            course_id: "C002",
            course_name: "Web Development Fundamentals",
            source_url: "https://www.example.com/web-development",
            description:
              "An overview of HTML, CSS, and JavaScript to build and style interactive web pages.",
          },
          {
            course_id: "C003",
            course_name: "Database Design",
            source_url: "https://www.example.com/database-design",
            description:
              "Understand how to design efficient databases, create ER diagrams, and write SQL queries.",
          },
        ];
        if (active) {
          setRecs(sample);
          setError("Using sample data (API unavailable)");
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    run();
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return recs;
    const q = query.toLowerCase();
    return recs.filter(
      (r) =>
        r.course_name.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.course_id.toLowerCase().includes(q)
    );
  }, [recs, query]);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-8">
      <header className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Recommended Courses
          </h1>
          <p className="text-muted-foreground">
            Curated suggestions to help you pick next course.
          </p>
          {error && <p className="mt-2 text-xs text-[--primary]">{error}</p>}
        </div>
        <div className="w-full max-w-md">
          <label htmlFor="search" className="sr-only">
            Search recommendations
          </label>
          <Input
            id="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, topic, or id…"
            className="bg-[--accent]"
          />
        </div>
      </header>

      {loading ? (
        <GridSkeleton />
      ) : filtered.length === 0 ? (
        <EmptyState reset={() => setQuery("")} />
      ) : (
        <section
          aria-live="polite"
          className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
        >
          {filtered.map((rec) => (
            <RecommendationCard key={rec.course_id} rec={rec} />
          ))}
        </section>
      )}
    </main>
  );
}

function RecommendationCard({ rec }: { rec: CourseRecommendation }) {
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(rec.source_url);
    } catch {
      // no-op
    }
  };

  return (
    <Card className="group border-border/80 bg-card shadow-sm transition hover:shadow-md">
      <CardHeader className="pb-0">
        <CardTitle className="text-lg">{rec.course_name}</CardTitle>
        <CardDescription className="text-xs">#{rec.course_id}</CardDescription>
        <CardAction>
          <Button
            variant="outline"
            size="sm"
            onClick={copyLink}
            aria-label="Copy course link"
            title="Copy link"
          >
            <LinkIcon className="size-4" />
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="pt-4">
        <p className="line-clamp-4 text-sm text-muted-foreground">
          {rec.description}
        </p>
      </CardContent>
      <CardFooter className="pt-0">
        <Button asChild className="gap-2" aria-label="Open course in a new tab">
          <a
            href={rec.source_url}
            target="_blank"
            rel="noopener noreferrer"
            title="Open course"
          >
            Open course <ExternalLink className="size-4" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-xl border border-border/80 bg-[--accent] p-6"
        >
          <div className="mb-3 h-5 w-2/3 rounded bg-border" />
          <div className="mb-1 h-3 w-20 rounded bg-border" />
          <div className="mt-4 space-y-2">
            <div className="h-3 w-full rounded bg-border" />
            <div className="h-3 w-[92%] rounded bg-border" />
            <div className="h-3 w-[85%] rounded bg-border" />
          </div>
          <div className="mt-6 h-9 w-32 rounded-md bg-(--primary)/20" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({ reset }: { reset: () => void }) {
  return (
    <div className="mx-auto max-w-md rounded-xl border border-dashed border-border p-8 text-center">
      <h2 className="text-base font-medium">No matches</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Try a different search term or clear the filter.
      </p>
      <Button onClick={reset} variant="ghost" className="mt-4">
        Reset
      </Button>
    </div>
  );
}

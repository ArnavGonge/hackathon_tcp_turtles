"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Link as LinkIcon, Search, Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";

type CourseRecommendation = {
  course_id: string;
  description: string;
  score: number;
  collaborative_score: number;
  content_score: number;
  confidence: string;
  avg_rating: number;
  tags: string[];
  reasons: string[];
};

export default function RecommendationPage() {
  const router = useRouter();
  const [recs, setRecs] = useState<CourseRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [userId, setUserId] = useState<string | null>(null);
  const [userTags, setUserTags] = useState<string[]>([]);

  useEffect(() => {
    let active = true;

    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);

      try {
        // Get the authenticated user
        const {
          data: { user },
          error: authError,
        } = await supabase.auth.getUser();

        if (authError || !user) {
          setError("Please log in to see recommendations");
          router.push("/login");
          return;
        }

        if (active) {
          setUserId(user.id);
        }

        // Get user profile from localStorage to retrieve tags
        const userProfileStr = localStorage.getItem("userProfile");
        let tags: string[] = [];

        if (userProfileStr) {
          const userProfile = JSON.parse(userProfileStr);
          tags = userProfile.tags || [];
          if (active) {
            setUserTags(tags);
          }
        }

        // Build the query parameters
        const params = new URLSearchParams({
          limit: "20",
        });

        if (tags.length > 0) {
          params.append("tags", tags.join(","));
        }

        // Call the FastAPI backend
        const backendUrl = `http://127.0.0.1:8000/api/recommendations/${
          user.id
        }?${params.toString()}`;
        console.log("Fetching from:", backendUrl);

        const res = await fetch(backendUrl, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!res.ok) {
          throw new Error(`Failed to fetch recommendations: ${res.status}`);
        }

        const data = await res.json();
        console.log("Received recommendations:", data);

        if (active) {
          setRecs(data.recommendations || []);
        }
      } catch (e: unknown) {
        console.error("Error fetching recommendations:", e);
        if (active) {
          setError(
            e instanceof Error ? e.message : "Failed to load recommendations"
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchRecommendations();

    return () => {
      active = false;
    };
  }, [router]);

  const filtered = useMemo(() => {
    if (!query.trim()) return recs;
    const q = query.toLowerCase();
    return recs.filter(
      (r) =>
        r.course_id.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.tags.some((tag) => tag.toLowerCase().includes(q))
    );
  }, [recs, query]);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-8">
      <section className="mb-8 rounded-2xl border bg-card p-6 shadow-xs sm:p-8">
        <header className="flex flex-col gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Recommended Courses
            </h1>
            <p className="text-muted-foreground">
              Personalized suggestions based on your profile and preferences.
            </p>
            {userId && (
              <p className="mt-1 text-xs text-muted-foreground">
                User ID: {userId}
              </p>
            )}
            {userTags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                <span className="text-xs text-muted-foreground">
                  Your tags:
                </span>
                {userTags.map((tag, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </div>
          <div className="w-full max-w-md">
            <label htmlFor="search" className="sr-only">
              Search recommendations
            </label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by course, topic, or tag..."
                className="bg-muted pl-9"
              />
            </div>
            <div className="mt-2 text-right text-xs text-muted-foreground">
              {filtered.length} result{filtered.length === 1 ? "" : "s"}
            </div>
          </div>
        </header>
      </section>

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
  return (
    <Card className="group border-border/80 bg-card shadow-sm ring-1 ring-transparent transition-all hover:-translate-y-0.5 hover:shadow-md hover:ring-primary/20 flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{rec.course_id}</CardTitle>
            <CardDescription className="text-xs mt-1">
              Score: {rec.score} | Confidence: {rec.confidence}
            </CardDescription>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            ⭐ {rec.avg_rating}
          </div>
        </div>
        {rec.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {rec.tags.slice(0, 3).map((tag, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {rec.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{rec.tags.length - 3}
              </Badge>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="line-clamp-3 text-sm text-muted-foreground mb-3">
          {rec.description}
        </p>

        {rec.reasons.length > 0 && (
          <div className="mt-auto pt-3 border-t">
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Why this course?
            </p>
            <ul className="text-xs text-muted-foreground space-y-1">
              {rec.reasons.slice(0, 2).map((reason, idx) => (
                <li key={idx} className="flex items-start gap-1">
                  <span className="text-primary">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse rounded-xl border border-border/80 bg-accent p-6"
        >
          <div className="mb-3 h-5 w-2/3 rounded bg-border" />
          <div className="mb-1 h-3 w-20 rounded bg-border" />
          <div className="mt-4 space-y-2">
            <div className="h-3 w-full rounded bg-border" />
            <div className="h-3 w-[92%] rounded bg-border" />
            <div className="h-3 w-[85%] rounded bg-border" />
          </div>
          <div className="mt-6 h-9 w-32 rounded-md bg-primary/20" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({ reset }: { reset: () => void }) {
  return (
    <div className="mx-auto max-w-md p-8 text-center">
      <h2 className="text-base font-medium">No recommendations found</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Try adjusting your search or update your profile tags.
      </p>
      <Button onClick={reset} variant="secondary" className="mt-4">
        Reset Search
      </Button>
    </div>
  );
}

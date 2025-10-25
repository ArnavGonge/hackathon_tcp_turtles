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
import { Search, Loader2, X, ExternalLink, Star } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";
import { useRouter } from "next/navigation";

type CourseRecommendation = {
  name: string;
  course_id: string;
  description: string;
  score: number;
  collaborative_score: number;
  content_score: number;
  confidence: string;
  avg_rating: number;
  tags: string[];
  reasons: string[];
  url?: string;
};

export default function RecommendationPage() {
  const router = useRouter();
  const [recs, setRecs] = useState<CourseRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [userId, setUserId] = useState<string | null>(null);
  const [userTags, setUserTags] = useState<string[]>([]);
  const [selectedCourse, setSelectedCourse] =
    useState<CourseRecommendation | null>(null);

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
        }?${params.toString()}&limit=3`;
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
            <div className="mt-2 text-xs text-muted-foreground">
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
            <RecommendationCard
              key={rec.course_id}
              rec={rec}
              onClick={() => setSelectedCourse(rec)}
            />
          ))}
        </section>
      )}

      {/* Course Detail Modal */}
      {selectedCourse && (
        <CourseDetailModal
          course={selectedCourse}
          onClose={() => setSelectedCourse(null)}
        />
      )}
    </main>
  );
}

function RecommendationCard({
  rec,
  onClick,
}: {
  rec: CourseRecommendation;
  onClick: () => void;
}) {
  return (
    <Card
      className="group border-border/80 bg-card shadow-sm ring-1 ring-transparent transition-all hover:-translate-y-0.5 hover:shadow-md hover:ring-primary/20 flex flex-col cursor-pointer"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg group-hover:text-primary transition-colors">
              {rec.course_id} - {rec.name}
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              Score: {rec.score}
            </CardDescription>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Star className="size-3 fill-yellow-400 text-yellow-400" />
            {rec.avg_rating}
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

        <div className="mt-4 text-xs text-primary group-hover:underline">
          Click to view details →
        </div>
      </CardContent>
    </Card>
  );
}

function CourseDetailModal({
  course,
  onClose,
}: {
  course: CourseRecommendation;
  onClose: () => void;
}) {
  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-card border border-border rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col animate-in zoom-in-95 slide-in-from-bottom-4 duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 pb-4 border-b">
          <div className="flex-1 pr-4">
            <h2 className="text-2xl font-semibold tracking-tight">
              {course.course_id}
            </h2>
            <p className="text-lg text-muted-foreground mt-1">{course.name}</p>
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onClose}
            className="shrink-0"
          >
            <X size={20} />
          </Button>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Rating and Scores */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-muted rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-primary">
                {course.score}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Overall Score
              </div>
            </div>
            <div className="bg-muted rounded-lg p-4 text-center">
              <div className="flex items-center justify-center gap-1 text-2xl font-bold">
                <Star className="size-5 fill-yellow-400 text-yellow-400" />
                {course.avg_rating}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Avg Rating
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Description</h3>
            <p className="text-muted-foreground leading-relaxed">
              {course.description || "No description available."}
            </p>
          </div>

          {/* Tags */}
          {course.tags.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {course.tags.map((tag, idx) => (
                  <Badge key={idx} variant="secondary" className="text-sm">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Recommendation Reasons */}
          {course.reasons.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">
                Why We Recommend This Course
              </h3>
              <ul className="space-y-2">
                {course.reasons.map((reason, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-3 text-muted-foreground"
                  >
                    <div className="size-2 rounded-full bg-primary mt-2 shrink-0" />
                    <span className="flex-1">{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 pt-4 border-t flex gap-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            Close
          </Button>
          {course.url ? (
            <Button
              className="flex-1 gap-2"
              onClick={() => window.open(course.url, "_blank")}
            >
              <ExternalLink size={16} />
              View Full Course Page
            </Button>
          ) : (
            <Button className="flex-1 gap-2" disabled>
              <ExternalLink size={16} />
              No Course Page Available
            </Button>
          )}
        </div>
      </div>
    </div>
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
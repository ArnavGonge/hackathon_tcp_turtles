"use client";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { courses } from "@prisma/client";
import { supabase } from "@/lib/supabaseClient";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Link from "next/link";
import { ChevronRight, CheckCircle2, Plus, Trash2, Search } from "lucide-react";
import { useRouter } from "next/navigation";

type CourseRating = {
  name: string;
  code: string;
  lecturer: number;
  joy: number;
  grading: number;
  material: number;
};

export default function CoursesPage() {
  const router = useRouter();
  const [courses, setCourses] = useState<courses[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Step management
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Search functionality
  const [searchQuery, setSearchQuery] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Step 1: Course selection
  const [selectedCourse, setSelectedCourse] = useState<{
    code: string;
    name: string;
  } | null>(null);

  // Step 2: Ratings
  const [lecturerRating, setLecturerRating] = useState(0);
  const [materialRating, setMaterialRating] = useState(0);
  const [overallJoy, setOverallJoy] = useState(0);
  const [gradingRating, setGradingRating] = useState(0);

  // Step 3: Review list
  const [courseList, setCourseList] = useState<CourseRating[]>([]);

  useEffect(() => {
    async function fetchCourses() {
      try {
        const res = await fetch("/api/courses");
        if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
        const data = await res.json();
        setCourses(data);
      } catch (err) {
        console.error("Error fetching courses:", err);
        setError("Failed to fetch courses");
      }
    }
    fetchCourses();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest("#courseSearch") && !target.closest(".dropdown-list")) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Reset form
  const resetForm = () => {
    setSelectedCourse(null);
    setLecturerRating(0);
    setMaterialRating(0);
    setOverallJoy(0);
    setGradingRating(0);
    setCurrentStep(1);
    setError("");
    setSearchQuery("");
    setIsDropdownOpen(false);
  };

  // Handle course selection
  const handleCourseSelect = (value: string) => {
    const parts = value.split(" - ");
    const code = parts[0];
    const name = parts.slice(1).join(" - ");
    setSelectedCourse({ code, name });
    setSearchQuery(`${code} - ${name}`);
    setIsDropdownOpen(false);
  };

  // Filter courses based on search query
  const filteredCourses = courses.filter((course) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      course.id.toLowerCase().includes(searchLower) ||
      (course.name?.toLowerCase() || "").includes(searchLower)
    );
  });

  // Move to ratings step
  const goToRatings = () => {
    if (!selectedCourse) {
      setError("Please select a course first");
      return;
    }
    setError("");
    setCurrentStep(2);
  };

  // Add course to list
  const addToList = () => {
    if (!selectedCourse) {
      setError("No course selected");
      return;
    }

    // Validation: at least one rating should be provided
    if (
      lecturerRating === 0 &&
      materialRating === 0 &&
      overallJoy === 0 &&
      gradingRating === 0
    ) {
      setError("Please provide at least one rating");
      return;
    }

    setCourseList([
      ...courseList,
      {
        name: selectedCourse.name,
        code: selectedCourse.code,
        lecturer: lecturerRating,
        joy: overallJoy,
        grading: gradingRating,
        material: materialRating,
      },
    ]);

    // Move to review step
    setCurrentStep(3);
    setError("");
  };

  // Remove course from list
  const removeCourse = (index: number) => {
    setCourseList(courseList.filter((_, i) => i !== index));
  };

  // Add another course
  const addAnother = () => {
    resetForm();
  };

  // Submit all courses
  const submitAllCourses = async () => {
    if (courseList.length === 0) {
      setError("Please add at least one course");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const {
        data: { session },
        error: sessionError,
      } = await supabase.auth.getSession();

      if (sessionError || !session) {
        setError("Not authenticated. Please log in again.");
        setLoading(false);
        return;
      }

      const token = session.access_token;

      const res = await fetch("/api/courses", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ courses: courseList }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to submit courses");
      }

      const result = await res.json();
      console.log("Success:", result);

      // Show success message
      setSubmitSuccess(true);

      // Clear everything after successful submission
      setCourseList([]);
      resetForm();

      // Redirect to recommendations after 2 seconds
      setTimeout(() => {
        router.push("/recommendation");
      }, 2000);
    } catch (err) {
      if (err instanceof Error) {
        setError(`Failed to submit courses: ${err.message}`);
      } else {
        setError("An unknown error occurred.");
      }
      console.error("Submit error:", err);
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-2xl rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="text-center text-2xl font-semibold">
            Add Your Courses
          </CardTitle>
          <p className="text-center text-sm text-muted-foreground mt-2">
            Tell us about the courses you've taken and rate your experience
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Progress Indicator */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div
              className={`flex items-center gap-2 ${
                currentStep >= 1 ? "text-primary" : "text-muted-foreground"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  currentStep >= 1
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                1
              </div>
              <span className="text-sm font-medium hidden sm:inline">
                Select
              </span>
            </div>

            <ChevronRight className="text-muted-foreground" size={20} />

            <div
              className={`flex items-center gap-2 ${
                currentStep >= 2 ? "text-primary" : "text-muted-foreground"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  currentStep >= 2
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                2
              </div>
              <span className="text-sm font-medium hidden sm:inline">
                Rate
              </span>
            </div>

            <ChevronRight className="text-muted-foreground" size={20} />

            <div
              className={`flex items-center gap-2 ${
                currentStep >= 3 ? "text-primary" : "text-muted-foreground"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  currentStep >= 3
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                3
              </div>
              <span className="text-sm font-medium hidden sm:inline">
                Review
              </span>
            </div>
          </div>

          {/* Step 1: Course Selection */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-5 duration-300">
              <div>
                <h3 className="text-lg font-medium mb-4">
                  Step 1: Select a Course
                </h3>
                <div className="space-y-2">
                  <label htmlFor="courseSearch" className="text-sm font-medium">
                    Search for Course
                  </label>
                  <div className="relative">
                    <Search
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                      size={18}
                    />
                    <Input
                      id="courseSearch"
                      type="text"
                      placeholder="Type to search (e.g., CS101 or Introduction)"
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value);
                        setIsDropdownOpen(true);
                        setSelectedCourse(null);
                      }}
                      onFocus={() => setIsDropdownOpen(true)}
                      className="pl-10"
                    />
                    
                    {/* Dropdown with filtered results */}
                    {isDropdownOpen && searchQuery && (
                      <div className="dropdown-list absolute z-10 w-full mt-1 max-h-60 overflow-auto bg-white dark:bg-muted border border-border rounded-md shadow-lg">
                        {filteredCourses.length > 0 ? (
                          filteredCourses.map((course) => (
                            <button
                              key={course.id}
                              type="button"
                              onClick={() =>
                                handleCourseSelect(`${course.id} - ${course.name}`)
                              }
                              className="w-full text-left px-4 py-2 hover:bg-accent hover:text-accent-foreground text-sm transition-colors"
                            >
                              <div className="font-medium">{course.id}</div>
                              <div className="text-xs text-muted-foreground">
                                {course.name}
                              </div>
                            </button>
                          ))
                        ) : (
                          <div className="px-4 py-3 text-sm text-muted-foreground">
                            No courses found matching "{searchQuery}"
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Start typing to filter courses by code or name
                  </p>
                </div>

                {selectedCourse && (
                  <div className="mt-4 p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="flex items-start gap-2">
                      <CheckCircle2
                        size={20}
                        className="text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0"
                      />
                      <div>
                        <p className="text-sm text-green-800 dark:text-green-200 font-medium">
                          Course selected
                        </p>
                        <p className="font-semibold text-green-900 dark:text-green-100 mt-1">
                          {selectedCourse.code} - {selectedCourse.name}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-4">
                <Button
                  onClick={goToRatings}
                  disabled={!selectedCourse}
                  className="gap-2"
                >
                  Next: Rate This Course
                  <ChevronRight size={16} />
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Ratings */}
          {currentStep === 2 && selectedCourse && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-5 duration-300">
              <div>
                <h3 className="text-lg font-medium mb-2">
                  Step 2: Rate Your Experience
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Rate {selectedCourse.code} on a scale of 0-5 (you can use
                  decimals like 3.5)
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Lecturer Quality
                    </label>
                    <Input
                      type="number"
                      min={0}
                      max={5}
                      step={0.5}
                      value={lecturerRating}
                      onChange={(e) => setLecturerRating(Number(e.target.value))}
                      placeholder="0.0"
                    />
                    <p className="text-xs text-muted-foreground">
                      How effective was the teaching?
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Material Quality
                    </label>
                    <Input
                      type="number"
                      min={0}
                      max={5}
                      step={0.5}
                      value={materialRating}
                      onChange={(e) => setMaterialRating(Number(e.target.value))}
                      placeholder="0.0"
                    />
                    <p className="text-xs text-muted-foreground">
                      How useful was the content?
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Overall Enjoyment
                    </label>
                    <Input
                      type="number"
                      min={0}
                      max={5}
                      step={0.5}
                      value={overallJoy}
                      onChange={(e) => setOverallJoy(Number(e.target.value))}
                      placeholder="0.0"
                    />
                    <p className="text-xs text-muted-foreground">
                      Did you enjoy taking this course?
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Grading Fairness
                    </label>
                    <Input
                      type="number"
                      min={0}
                      max={5}
                      step={0.5}
                      value={gradingRating}
                      onChange={(e) => setGradingRating(Number(e.target.value))}
                      placeholder="0.0"
                    />
                    <p className="text-xs text-muted-foreground">
                      How fair was the grading system?
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-4">
                <Button onClick={() => setCurrentStep(1)} variant="outline">
                  Back
                </Button>
                <Button onClick={addToList} className="gap-2">
                  Add to List
                  <CheckCircle2 size={16} />
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Review and Submit */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-5 duration-300">
              <div>
                <h3 className="text-lg font-medium mb-2">
                  Step 3: Review Your Courses
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  You can add more courses or submit everything
                </p>

                {courseList.length > 0 ? (
                  <div className="space-y-3">
                    {courseList.map((course, index) => (
                      <div
                        key={index}
                        className="bg-white dark:bg-muted rounded-lg p-4 shadow-sm border border-gray-200"
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <p className="font-semibold text-gray-800 dark:text-gray-100">
                              {course.code}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {course.name}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => removeCourse(index)}
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Lecturer:
                            </span>
                            <span className="font-medium">{course.lecturer}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Material:
                            </span>
                            <span className="font-medium">{course.material}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Enjoyment:
                            </span>
                            <span className="font-medium">{course.joy}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">
                              Grading:
                            </span>
                            <span className="font-medium">{course.grading}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No courses added yet
                  </div>
                )}
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-4">
                <Button
                  onClick={addAnother}
                  variant="outline"
                  className="flex-1 gap-2"
                >
                  <Plus size={16} />
                  Add Another Course
                </Button>
                <Button
                  onClick={submitAllCourses}
                  disabled={loading || courseList.length === 0}
                  className="flex-1 gap-2"
                >
                  {loading ? (
                    "Submitting..."
                  ) : (
                    <>
                      <CheckCircle2 size={16} />
                      Submit All ({courseList.length})
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex justify-center border-t pt-6">
          {submitSuccess ? (
            <div className="text-center space-y-2 w-full">
              <div className="flex items-center justify-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle2 size={24} />
                <p className="text-lg font-semibold">
                  Courses submitted successfully!
                </p>
              </div>
              <p className="text-sm text-muted-foreground">
                Redirecting to recommendations...
              </p>
            </div>
          ) : currentStep === 3 && courseList.length > 0 ? (
            <Button
              onClick={() => router.push("/recommendation")}
              variant="link"
              className="text-sm"
            >
              Skip to Recommendations →
            </Button>
          ) : (
            <Link href="/recommendation">
              <Button variant="link" className="text-sm">
                View Recommendations →
              </Button>
            </Link>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
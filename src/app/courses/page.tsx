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

export default function CoursesPage() {
  const [courses, setCourses] = useState<courses[]>([]);
  const [courseCode, setCourseCode] = useState("");
  const [lecturerRating, setLecturerRating] = useState(0);
  const [materialRating, setMaterialRating] = useState(0);
  const [overallJoy, setOverallJoy] = useState(0);
  const [gradingRating, setGradingRating] = useState(0);
  const [courseList, setCourseList] = useState<
    {
      name: string;
      code: string;
      lecturer: number;
      joy: number;
      grading: number;
      material: number;
    }[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchCourses() {
      try {
        const res = await fetch("/api/courses");
        if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
        const data = await res.json();
        console.log("Fetched courses:", data);
        setCourses(data);
      } catch (err) {
        console.error("Error fetching courses:", err);
        setError("Failed to fetch courses");
      }
    }
    fetchCourses();
  }, []);

  const addCourse = () => {
    if (!courseCode) {
      setError("Please select a course.");
      return;
    }
    setCourseList([
      ...courseList,
      {
        name: courseCode,
        code: courseCode,
        lecturer: lecturerRating,
        joy: overallJoy,
        grading: gradingRating,
        material: materialRating,
      },
    ]);
    setCourseCode("");
    setLecturerRating(0);
    setMaterialRating(0);
    setOverallJoy(0);
    setGradingRating(0);
    setError("");
  };

  const submitCourses = async () => {
    if (courseList.length === 0) {
      setError("Add at least one course.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      // Get the current session from Supabase
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
      console.log("Submitting courses:", courseList);
      console.log("Token present:", !!token);

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
      setCourseList([]);

      // Optionally refresh the courses list
      const updatedRes = await fetch("/api/courses");
      const updatedData = await updatedRes.json();
      setCourses(updatedData);
    } catch (err) {
      if (err instanceof Error) {
        setError(`Failed to add courses. ${err.message}`);
      } else {
        setError("An unknown error occurred.");
      }
      console.error("Submit error:", err);
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="text-center text-2xl font-semibold">
            Add Courses
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="courseCode">Course Code</label>
            <Select value={courseCode} onValueChange={setCourseCode}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a course" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {courses.length === 0 ? (
                    <SelectItem value="loading" disabled>
                      Loading courses...
                    </SelectItem>
                  ) : (
                    courses.map((course) => (
                      <SelectItem key={course.id} value={course.id}>
                        {course.id}
                      </SelectItem>
                    ))
                  )}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label>Lecturer Rating</label>
              <Input
                type="number"
                min={0}
                max={5}
                step={0.5}
                value={lecturerRating}
                onChange={(e) => setLecturerRating(Number(e.target.value))}
              />
            </div>
            <div>
              <label>Material Rating</label>
              <Input
                type="number"
                min={0}
                max={5}
                step={0.5}
                value={materialRating}
                onChange={(e) => setMaterialRating(Number(e.target.value))}
              />
            </div>
            <div>
              <label>Overall Rating</label>
              <Input
                type="number"
                min={0}
                max={5}
                step={0.5}
                value={overallJoy}
                onChange={(e) => setOverallJoy(Number(e.target.value))}
              />
            </div>
            <div>
              <label>Grading Rating</label>
              <Input
                type="number"
                min={0}
                max={5}
                step={0.5}
                value={gradingRating}
                onChange={(e) => setGradingRating(Number(e.target.value))}
              />
            </div>
          </div>

          <Button type="button" onClick={addCourse} className="w-full">
            Add to List
          </Button>

          {courseList.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-medium">Courses to Add:</h3>
              <ul className="space-y-2">
                {courseList.map((c, i) => (
                  <li
                    key={i}
                    className="bg-white dark:bg-muted rounded-lg p-3 shadow-sm flex flex-col space-y-1 border border-gray-200"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-gray-800 dark:text-gray-100">
                        {c.code}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {c.name}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <div>
                        <span className="font-medium">Lecturer:</span>{" "}
                        {c.lecturer}
                      </div>
                      <div>
                        <span className="font-medium">Material:</span>{" "}
                        {c.material}
                      </div>
                      <div>
                        <span className="font-medium">Overall:</span> {c.joy}
                      </div>
                      <div>
                        <span className="font-medium">Grading:</span>{" "}
                        {c.grading}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button
            type="button"
            onClick={submitCourses}
            className="w-full"
            disabled={loading}
          >
            {loading ? "Submitting..." : "Submit All"}
          </Button>
        </CardContent>
        <CardFooter>
          <Link href="/recommendation" className="w-full text-center">
            <Button variant="link" className="text-sm">
              Go to Recommendations
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}

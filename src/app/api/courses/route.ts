import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabaseClient";

export async function GET() {
  try {
    const courses = await prisma.courses.findMany();
    return NextResponse.json(courses);
  } catch (error) {
    console.error("Error fetching courses:", error);
    console.error(error);
    return NextResponse.json(
      { error: "Failed to fetch courses" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  console.log("Received POST request to /api/courses");
  try {
    const token = request.headers.get("Authorization")?.replace("Bearer ", "");
    if (!token) {
      console.error("No access token provided");
      return NextResponse.json(
        { error: "No access token provided" },
        { status: 401 }
      );
    }

    // Verify token with Supabase
    const { data: user, error: userError } = await supabase.auth.getUser(token);
    if (userError || !user?.user) {
      console.error("Invalid token:", userError);
      return NextResponse.json({ error: "Invalid token" }, { status: 401 });
    }
    const userId = user.user.id;

    // Grab courses array from request body
    const { courses } = await request.json();
    console.log("Received courses for user:", userId, courses);

    // Validate that courses is an array and not empty
    if (!Array.isArray(courses) || courses.length === 0) {
      console.error("Invalid request: courses must be a non-empty array");
      return NextResponse.json(
        { error: "Invalid request: courses must be a non-empty array" },
        { status: 400 }
      );
    }

    // Create all ratings using createMany for better performance
    const newRatings = await prisma.ratings.createMany({
      data: courses.map((course) => ({
        user_id: userId,
        course_id: course.code,
        lecturer: course.lecturer,
        joy: course.joy,
        grading: course.grading,
        material: course.material,
      })),
      skipDuplicates: true, // Skip if user already rated this course
    });

    const newCourses = await prisma.history.createMany({
      data: courses.map((course) => ({
        user_id: userId,
        course_id: course.code,
      })),
      skipDuplicates: true,
    });

    return NextResponse.json(
      {
        message: "Ratings and courses added successfully",
        ratings_count: newRatings.count,
        courses_count: newCourses.count,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Error adding course ratings:", error);
    return NextResponse.json(
      { error: "Failed to add course ratings" },
      { status: 500 }
    );
  }
}

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

// export async function POST(request: Request) {
//   try {
//     // Grab access token from request headers
//     const token = request.headers.get("Authorization")?.replace("Bearer ", "");

//     if (!token) {
//       return NextResponse.json(
//         { error: "No access token provided" },
//         { status: 401 }
//       );
//     }

//     // Verify token with Supabase
//     const { data: user, error: userError } = await supabase.auth.getUser(token);

//     if (userError || !user?.user) {
//       return NextResponse.json({ error: "Invalid token" }, { status: 401 });
//     }

//     const userId = user.user.id;

//     // Grab rating data from request body
//     const { code, rating, overall, grading, material } = await request.json();

// const newCourse = await prisma.ratings.create({
//   data: {
//     user_id: userId,
//     course_id: code,
//     joy: rating,
//     grading,
//     material,
//     Date: new Date(),
//   },
// });

//     return NextResponse.json(newCourse, { status: 201 });
//   } catch (error) {
//     console.error("Error adding course rating:", error);
//     return NextResponse.json(
//       { error: "Failed to add course rating" },
//       { status: 500 }
//     );
//   }
// }

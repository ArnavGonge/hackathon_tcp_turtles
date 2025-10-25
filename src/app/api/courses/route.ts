import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

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

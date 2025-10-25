import { prisma } from "@/lib/prisma";

// Example usage of Prisma with your database schema

// ============================================
// USERS
// ============================================

// Get all users
export async function getAllUsers() {
  return await prisma.users.findMany({
    include: {
      ratings: true,
      history: true,
    },
  });
}

// Get user by ID
export async function getUserById(id: number) {
  return await prisma.users.findUnique({
    where: { id },
    include: {
      ratings: true,
      history: {
        include: {
          courses: true,
        },
      },
    },
  });
}

// Create a new user
export async function createUser(username: string, bio?: string) {
  return await prisma.users.create({
    data: {
      username,
      bio,
    },
  });
}

// ============================================
// COURSES
// ============================================

// Get all courses with ratings
export async function getAllCourses() {
  return await prisma.courses.findMany({
    include: {
      ratings: true,
      course_tag: {
        include: {
          tags: true,
        },
      },
      sem_offered: {
        include: {
          sems: true,
        },
      },
    },
  });
}

// Get course by ID
export async function getCourseById(id: string) {
  return await prisma.courses.findUnique({
    where: { id },
    include: {
      ratings: true,
      course_tag: {
        include: {
          tags: true,
        },
      },
      listings: {
        include: {
          programs: true,
        },
      },
      prereqs_prereqs_course_idTocourses: {
        include: {
          courses_prereqs_prereq_idTocourses: true,
        },
      },
    },
  });
}

// Search courses by description
export async function searchCourses(query: string) {
  return await prisma.courses.findMany({
    where: {
      description: {
        contains: query,
        mode: "insensitive",
      },
    },
    include: {
      course_tag: {
        include: {
          tags: true,
        },
      },
    },
  });
}

// ============================================
// RATINGS
// ============================================

// Create a rating
export async function createRating(
  courseId: string,
  userId: number,
  data: {
    lecturer?: number;
    material?: number;
    grading?: number;
    joy?: number;
  }
) {
  return await prisma.ratings.create({
    data: {
      course_id: courseId,
      user_id: userId,
      ...data,
    },
  });
}

// Get course ratings
export async function getCourseRatings(courseId: string) {
  return await prisma.ratings.findMany({
    where: { course_id: courseId },
    include: {
      users: true,
    },
    orderBy: {
      created_at: "desc",
    },
  });
}

// Update rating
export async function updateRating(
  id: number,
  data: {
    lecturer?: number;
    material?: number;
    grading?: number;
    joy?: number;
  }
) {
  return await prisma.ratings.update({
    where: { id },
    data,
  });
}

// ============================================
// TAGS
// ============================================

// Get all tags
export async function getAllTags() {
  return await prisma.tags.findMany({
    include: {
      course_tag: {
        include: {
          courses: true,
        },
      },
    },
  });
}

// Get courses by tag
export async function getCoursesByTag(tagId: number) {
  return await prisma.course_tag.findMany({
    where: { tag_id: tagId },
    include: {
      courses: true,
      tags: true,
    },
  });
}

// ============================================
// PROGRAMS
// ============================================

// Get all programs
export async function getAllPrograms() {
  return await prisma.programs.findMany({
    include: {
      listings: {
        include: {
          courses: true,
        },
      },
    },
  });
}

// Get program courses
export async function getProgramCourses(progId: string) {
  return await prisma.listings.findMany({
    where: { prog_id: progId },
    include: {
      courses: true,
    },
  });
}

// ============================================
// USER HISTORY
// ============================================

// Add course to user history
export async function addCourseToHistory(userId: number, courseId: string) {
  return await prisma.history.create({
    data: {
      user_id: userId,
      course_id: courseId,
    },
  });
}

// Get user course history
export async function getUserHistory(userId: number) {
  return await prisma.history.findMany({
    where: { user_id: userId },
    include: {
      courses: true,
    },
  });
}

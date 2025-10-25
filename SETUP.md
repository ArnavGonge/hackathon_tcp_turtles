# Supabase + Prisma Setup Guide

This project uses Supabase for authentication and Prisma as the ORM.

## Setup Instructions

### 1. Configure Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Then fill in your Supabase credentials:

- **NEXT_PUBLIC_SUPABASE_URL**: Found in your Supabase project settings
- **NEXT_PUBLIC_SUPABASE_ANON_KEY**: Found in your Supabase project settings (API section)
- **DATABASE_URL**: Your Supabase PostgreSQL connection string
  - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres`
  - Found in Supabase Project Settings > Database > Connection string (URI)
- **DIRECT_URL**: Same as DATABASE_URL (for Prisma migrations)

### 2. Pull Your Existing Database Schema

Since you already have a database in Supabase, introspect it to generate your Prisma schema:

```bash
npm run db:pull
```

This will update `prisma/schema.prisma` with your existing tables.

### 3. Generate Prisma Client

```bash
npm run db:generate
```

This creates the Prisma Client based on your schema.

### 4. Using Prisma in Your Code

Import the Prisma client from `@/lib/prisma`:

```typescript
import { prisma } from "@/lib/prisma";

// Example: Get all users
const users = await prisma.user.findMany();
```

### 5. Using Supabase Client

**Client Components:**

```typescript
import { createClient } from "@/utils/supabase/client";

const supabase = createClient();
const { data, error } = await supabase.auth.signInWithPassword({
  email: "user@example.com",
  password: "password",
});
```

**Server Components:**

```typescript
import { createClient } from "@/utils/supabase/server";

const supabase = await createClient();
const {
  data: { user },
} = await supabase.auth.getUser();
```

## Available Scripts

- `npm run db:pull` - Pull schema from your existing Supabase database
- `npm run db:push` - Push schema changes to database (use with caution)
- `npm run db:generate` - Generate Prisma Client
- `npm run db:studio` - Open Prisma Studio (database GUI)

## Best Practices

1. **Use Supabase for Auth**: Authentication, user management, and RLS policies
2. **Use Prisma for Data**: Type-safe database queries with excellent DX
3. **Keep Schema in Sync**: Run `db:pull` after making changes in Supabase dashboard
4. **Use RLS Policies**: Set up Row Level Security in Supabase for data protection

## Next Steps

1. Run `npm run db:pull` to introspect your existing database
2. Run `npm run db:generate` to generate the Prisma Client
3. Start building with type-safe database queries!

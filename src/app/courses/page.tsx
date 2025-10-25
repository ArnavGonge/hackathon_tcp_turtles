"use client";

import { useUser } from "@/components/context/UserContext";

export default function Profile() {
  const { user, loading, signOut } = useUser();

  if (loading) return <p>Loading...</p>;
  if (!user) return <p>Please log in</p>;

  return (
    <div>
      <p>Welcome, {user.email}</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  );
}
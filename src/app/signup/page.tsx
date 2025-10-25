"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, ChevronRight, User, Lock, FileText, Tags } from "lucide-react";
import Link from "next/link";

interface Tag {
  id: string;
  name: string;
}

export default function SignupPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);
  
  // Step 1: Account credentials
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Step 2: Profile info
  const [description, setDescription] = useState("");
  
  // Step 3: Tags
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [tagSearchQuery, setTagSearchQuery] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [loadingTags, setLoadingTags] = useState(true);
  const [error, setError] = useState("");
  const [signupSuccess, setSignupSuccess] = useState(false);

  useEffect(() => {
    async function fetchTags() {
      try {
        const res = await fetch("/api/tags");
        if (!res.ok) throw new Error("Failed to fetch tags");
        const data = await res.json();
        setAvailableTags(data);
      } catch (err) {
        console.error("Error fetching tags:", err);
        setError("Failed to load tags");
      } finally {
        setLoadingTags(false);
      }
    }
    fetchTags();
  }, []);

  const toggleTag = (tagId: string) => {
    if (selectedTags.includes(tagId)) {
      setSelectedTags(selectedTags.filter((id) => id !== tagId));
    } else {
      setSelectedTags([...selectedTags, tagId]);
    }
  };

  const removeTag = (tagId: string) => {
    setSelectedTags(selectedTags.filter((id) => id !== tagId));
  };

  const getSelectedTagNames = () => {
    return availableTags.filter((tag) => selectedTags.includes(tag.id));
  };

  // Filter tags based on search query
  const filteredTags = availableTags.filter((tag) =>
    tag.name.toLowerCase().includes(tagSearchQuery.toLowerCase())
  );

  // Validation for Step 1
  const validateStep1 = () => {
    if (!email || !password || !confirmPassword) {
      setError("Please fill in all fields");
      return false;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return false;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return false;
    }
    setError("");
    return true;
  };

  const goToStep2 = () => {
    if (validateStep1()) {
      setCurrentStep(2);
    }
  };

  const goToStep3 = () => {
    setCurrentStep(3);
    setError("");
  };

  const handleSignup = async () => {
    setLoading(true);
    setError("");

    const { data, error: signupError } = await supabase.auth.signUp({
      email,
      password,
    });

    if (signupError) {
      setError(signupError.message);
      setLoading(false);
      return;
    }

    // Save description and tags to localStorage
    if (data.user) {
      const selectedTagNames = availableTags
        .filter((tag) => selectedTags.includes(tag.id))
        .map((tag) => tag.name);

      const userProfile = {
        description,
        tags: selectedTagNames,
        userId: data.user.id,
      };
      localStorage.setItem("userProfile", JSON.stringify(userProfile));
      console.log("Saved user profile:", userProfile);
    }

    // Show success message
    setSignupSuccess(true);
    setLoading(false);
    
    // Auto-redirect to courses page after 2 seconds
    setTimeout(() => {
      router.push("/courses");
    }, 2000);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-2xl rounded-2xl shadow-sm">
        <CardHeader>
          <CardTitle className="text-center text-2xl font-semibold">
            Create Your Account
          </CardTitle>
          <p className="text-center text-sm text-muted-foreground mt-2">
            Set up your profile to get personalized course recommendations
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {signupSuccess ? (
            // Success Message
            <div className="py-12 text-center space-y-4 animate-in fade-in zoom-in-95 duration-300">
              <div className="flex justify-center">
                <div className="rounded-full bg-green-100 dark:bg-green-950 p-6">
                  <CheckCircle2 size={64} className="text-green-600 dark:text-green-400" />
                </div>
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-semibold text-green-600 dark:text-green-400">
                  Account Created Successfully!
                </h3>
                <p className="text-muted-foreground">
                  Welcome aboard! Redirecting you to add courses...
                </p>
                <div className="flex items-center justify-center gap-2 mt-4">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                </div>
              </div>
              <div className="text-xs text-muted-foreground mt-6 p-4 bg-muted/50 rounded-lg border">
                <p>📧 Please check your email to confirm your account</p>
                <p className="mt-1">You can start using the app right away!</p>
              </div>
            </div>
          ) : (
            <>
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
                    <User size={16} />
                  </div>
                  <span className="text-sm font-medium hidden sm:inline">
                    Account
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
                    <FileText size={16} />
                  </div>
                  <span className="text-sm font-medium hidden sm:inline">
                    Profile
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
                    <Tags size={16} />
                  </div>
                  <span className="text-sm font-medium hidden sm:inline">
                    Interests
                  </span>
                </div>
              </div>

              {/* Step 1: Account Creation */}
              {currentStep === 1 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-right-5 duration-300">
                  <div>
                    <h3 className="text-lg font-medium mb-4">
                      Step 1: Create Your Account
                    </h3>
                    
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label htmlFor="email" className="text-sm font-medium">
                          Email Address
                        </label>
                        <Input
                          id="email"
                          type="email"
                          placeholder="you@example.com"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          required
                        />
                        <p className="text-xs text-muted-foreground">
                          You'll need to confirm this email address
                        </p>
                      </div>

                      <div className="space-y-2">
                        <label htmlFor="password" className="text-sm font-medium">
                          Password
                        </label>
                        <Input
                          id="password"
                          type="password"
                          placeholder="At least 6 characters"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          required
                          minLength={6}
                        />
                      </div>

                      <div className="space-y-2">
                        <label htmlFor="confirmPassword" className="text-sm font-medium">
                          Confirm Password
                        </label>
                        <Input
                          id="confirmPassword"
                          type="password"
                          placeholder="Re-enter your password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          required
                          minLength={6}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button onClick={goToStep2} className="gap-2">
                      Next: Profile Info
                      <ChevronRight size={16} />
                    </Button>
                  </div>
                </div>
              )}

              {/* Step 2: Profile Description */}
              {currentStep === 2 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-right-5 duration-300">
                  <div>
                    <h3 className="text-lg font-medium mb-2">
                      Step 2: Tell Us About Yourself
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      This helps us understand your background and interests (optional)
                    </p>

                    <div className="space-y-2">
                      <label htmlFor="description" className="text-sm font-medium">
                        Bio / Description
                      </label>
                      <Textarea
                        id="description"
                        placeholder="E.g., I'm a computer science student interested in web development and machine learning..."
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        rows={5}
                        className="resize-none"
                      />
                      <p className="text-xs text-muted-foreground">
                        {description.length} characters
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button onClick={() => setCurrentStep(1)} variant="outline">
                      Back
                    </Button>
                    <Button onClick={goToStep3} className="gap-2">
                      Next: Select Interests
                      <ChevronRight size={16} />
                    </Button>
                  </div>
                </div>
              )}

              {/* Step 3: Tag Selection */}
              {currentStep === 3 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-right-5 duration-300">
                  <div>
                    <h3 className="text-lg font-medium mb-2">
                      Step 3: Choose Your Interests
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Select topics you're interested in to get better recommendations
                    </p>

                    {/* Search box for tags */}
                    <div className="space-y-2 mb-4">
                      <Input
                        type="text"
                        placeholder="Search interests... (e.g., web development, AI)"
                        value={tagSearchQuery}
                        onChange={(e) => setTagSearchQuery(e.target.value)}
                        className="mb-3"
                      />
                    </div>

                    {/* Selected tags display */}
                    {selectedTags.length > 0 && (
                      <div className="mb-4 p-4 bg-muted/50 rounded-lg border">
                        <p className="text-sm font-medium mb-2">
                          Selected ({selectedTags.length}):
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {getSelectedTagNames().map((tag) => (
                            <Badge
                              key={tag.id}
                              variant="default"
                              className="flex items-center gap-1 cursor-pointer hover:bg-primary/80"
                              onClick={() => removeTag(tag.id)}
                            >
                              {tag.name}
                              <span className="text-xs ml-1">×</span>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Available tags */}
                    {loadingTags ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        Loading interests...
                      </p>
                    ) : (
                      <div className="border rounded-lg max-h-80 overflow-y-auto">
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-4">
                          {filteredTags.length === 0 ? (
                            <p className="text-sm text-muted-foreground col-span-full text-center py-4">
                              No interests found matching "{tagSearchQuery}"
                            </p>
                          ) : (
                            filteredTags.map((tag) => (
                              <button
                                key={tag.id}
                                type="button"
                                onClick={() => toggleTag(tag.id)}
                                className={`text-left px-3 py-2 rounded-md text-sm transition-all ${
                                  selectedTags.includes(tag.id)
                                    ? "bg-primary text-primary-foreground font-medium"
                                    : "bg-muted hover:bg-muted/80"
                                }`}
                              >
                                <div className="flex items-center gap-2">
                                  {selectedTags.includes(tag.id) && (
                                    <CheckCircle2 size={14} />
                                  )}
                                  <span>{tag.name}</span>
                                </div>
                              </button>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-between pt-4">
                    <Button onClick={() => setCurrentStep(2)} variant="outline">
                      Back
                    </Button>
                    <Button
                      onClick={handleSignup}
                      disabled={loading}
                      className="gap-2"
                    >
                      {loading ? (
                        "Creating Account..."
                      ) : (
                        <>
                          <CheckCircle2 size={16} />
                          Create Account
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
            </>
          )}
        </CardContent>

        {!signupSuccess && (
          <div className="px-6 pb-6 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/" className="text-primary hover:underline font-medium">
                Log in
              </Link>
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
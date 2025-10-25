-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.course_tag (
  course_id text NOT NULL,
  tag_id integer NOT NULL,
  CONSTRAINT course_tag_pkey PRIMARY KEY (course_id, tag_id),
  CONSTRAINT course_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id),
  CONSTRAINT course_tag_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id)
);
CREATE TABLE public.courses (
  id text NOT NULL UNIQUE,
  description text,
  rating double precision DEFAULT 0.0,
  source_url text DEFAULT ''::text,
  name text,
  CONSTRAINT courses_pkey PRIMARY KEY (id)
);
CREATE TABLE public.history (
  course_id character varying NOT NULL,
  user_id uuid NOT NULL,
  CONSTRAINT history_pkey PRIMARY KEY (course_id, user_id),
  CONSTRAINT history_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id),
  CONSTRAINT history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.listings (
  prog_id character varying NOT NULL,
  course_id character varying NOT NULL,
  CONSTRAINT listings_pkey PRIMARY KEY (prog_id, course_id),
  CONSTRAINT listings_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id),
  CONSTRAINT listings_prog_id_fkey FOREIGN KEY (prog_id) REFERENCES public.programs(id)
);
CREATE TABLE public.prereqs (
  course_id text NOT NULL,
  prereq_id text NOT NULL,
  CONSTRAINT prereqs_pkey PRIMARY KEY (course_id, prereq_id),
  CONSTRAINT prereqs_prereq_id_fkey FOREIGN KEY (prereq_id) REFERENCES public.courses(id),
  CONSTRAINT prereqs_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id)
);
CREATE TABLE public.programs (
  id text NOT NULL,
  name text NOT NULL,
  CONSTRAINT programs_pkey PRIMARY KEY (id)
);
CREATE TABLE public.ratings (
  id integer NOT NULL DEFAULT nextval('ratings_id_seq'::regclass),
  course_id text NOT NULL,
  lecturer integer CHECK (lecturer >= 1 AND lecturer <= 5),
  material integer CHECK (material >= 1 AND material <= 5),
  grading integer CHECK (grading >= 1 AND grading <= 5),
  joy integer CHECK (joy >= 1 AND joy <= 5),
  created_at timestamp with time zone DEFAULT now(),
  user_id uuid NOT NULL,
  CONSTRAINT ratings_pkey PRIMARY KEY (id),
  CONSTRAINT ratings_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id),
  CONSTRAINT ratings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.sem_offered (
  course_id text NOT NULL,
  sem_name text NOT NULL,
  CONSTRAINT sem_offered_pkey PRIMARY KEY (course_id, sem_name),
  CONSTRAINT offered_in_sem_name_fkey FOREIGN KEY (sem_name) REFERENCES public.sems(name),
  CONSTRAINT offered_in_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id)
);
CREATE TABLE public.sems (
  name text NOT NULL UNIQUE,
  date_start timestamp with time zone NOT NULL UNIQUE,
  CONSTRAINT sems_pkey PRIMARY KEY (name)
);
CREATE TABLE public.tags (
  id integer NOT NULL DEFAULT nextval('tags_id_seq'::regclass),
  name text NOT NULL,
  CONSTRAINT tags_pkey PRIMARY KEY (id)
);
CREATE TABLE public.users (
  id uuid NOT NULL,
  username text NOT NULL,
  bio text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);